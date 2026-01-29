"""
Email management for proton-mail-bridge-client.

Handles listing, reading, sending, and deleting emails from ProtonMail via IMAP/SMTP.
"""

import email
import email.policy
import logging
import re
import uuid
from dataclasses import replace
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .folder import FolderManager

from inscriptis import get_text  # type: ignore[import-untyped]
from inscriptis.css_profiles import CSS_PROFILES  # type: ignore[import-untyped]
from inscriptis.model.config import ParserConfig  # type: ignore[import-untyped]

from .connection import IMAPConnectionManager
from .exceptions import (
    BridgeConnectionError,
    EmailDeleteError,
    EmailError,
    EmailNotFoundError,
    EmailSendError,
    FolderNotFoundError,
    InvalidEmailFormatError,
    InvalidLabelNameError,
    InvalidRecipientError,
    LabelNotFoundError,
)
from .folder import _quote_folder_name
from .models import Email, EmailMetadata
from .smtp_connection import SMTPConnectionManager
from .utils import (
    decode_header,
    is_readonly_folder,
    parse_address_list,
    parse_email_date,
    parse_imap_envelope,
    safe_decode_bytes,
    translate_imap_error,
    validate_email_uid,
)

logger = logging.getLogger(__name__)


def _html_to_text(html_content: str) -> str:
    """
    Convert HTML to plain text using inscriptis.

    Args:
        html_content: HTML string to convert

    Returns:
        Plain text representation of HTML with links preserved
    """
    config = ParserConfig(css=CSS_PROFILES["strict"], display_links=True)
    text: str = get_text(html_content, config=config)
    return text.strip()


def _escape_imap_string(value: str) -> str:
    """
    Escape special characters for IMAP quoted strings per RFC 3501.

    IMAP quoted strings use backslash as escape character. Both backslash
    and double-quote must be escaped to prevent IMAP command injection.

    Args:
        value: String to escape

    Returns:
        Escaped string safe for use in IMAP quoted strings
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _date_sort_key(metadata: EmailMetadata) -> tuple[int, datetime]:
    """
    Return a sortable key for email date.

    Handles None, timezone-aware, and timezone-naive datetimes consistently.
    Emails without dates sort to the end (after all dated emails).

    Args:
        metadata: EmailMetadata object to extract date from

    Returns:
        Tuple of (priority, normalized_datetime) for sorting
    """
    if metadata.date is None:
        return (1, datetime.min.replace(tzinfo=None))
    return (
        0,
        metadata.date.replace(tzinfo=None) if metadata.date.tzinfo else metadata.date,
    )


class EmailManager:
    """
    Manages email operations (listing, reading, sending, and deleting).

    Provides methods for listing emails with filtering/pagination,
    reading full email content, sending emails via SMTP, and deleting emails via IMAP.

    Attributes:
        imap_connection_manager: IMAP connection manager instance
        smtp_connection_manager: SMTP connection manager instance
    """

    def __init__(
        self,
        imap_connection_manager: IMAPConnectionManager,
        smtp_connection_manager: SMTPConnectionManager,
        folder_manager: "FolderManager | None" = None,
    ):
        """
        Initialize EmailManager.

        Args:
            imap_connection_manager: IMAP connection manager for Bridge access
            smtp_connection_manager: SMTP connection manager for Bridge access
            folder_manager: Folder manager for folder name translation
        """
        self._imap_connection_manager = imap_connection_manager
        self._smtp_connection_manager = smtp_connection_manager
        self._folder_manager = folder_manager
        # For backwards compatibility with existing code
        self._connection_manager = imap_connection_manager

    def list_mails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        sort_by_date: str = "desc",
        include_labels: bool = False,
    ) -> list[EmailMetadata]:
        """
        List emails in a folder with filtering and pagination.

        Args:
            folder: Folder name (default: "INBOX")
            limit: Maximum emails to return (default: 50)
            offset: Number of emails to skip (default: 0)
            unread_only: Only return unread emails (default: False)
            sort_by_date: Sort order - "asc" or "desc" (default: "desc")
            include_labels: If True, populate the labels field for each email.
                **Performance Note:** This requires checking each email against
                all label folders, resulting in (N emails x M labels) IMAP queries.
                While ProtonMail Bridge caches data locally, this can still be
                slow for large mailboxes with many labels. Default is False.

        Returns:
            List of EmailMetadata objects

        Raises:
            FolderNotFoundError: If folder doesn't exist
            BridgeConnectionError: If connection to Bridge fails
            ValueError: If limit <= 0 or sort_by_date invalid
        """
        # Validate inputs
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        # Make sort_by_date case-insensitive (BUG #6 fix)
        sort_by_date = sort_by_date.lower()
        if sort_by_date not in ("asc", "desc"):
            raise ValueError('sort_by_date must be "asc" or "desc" (case-insensitive)')

        try:
            # Select folder
            self._select_folder(folder)

            # Search for emails
            email_ids = self._search_emails(unread_only)

            # Sort by date (IMAP returns UIDs in insertion order, not date order)
            # For simplicity, we'll sort after fetching metadata
            # In production, could use IMAP SORT extension if available

            # Apply pagination
            if sort_by_date == "desc":
                email_ids = list(reversed(email_ids))

            paginated_ids = email_ids[offset : offset + limit]

            # Fetch metadata for paginated emails
            if not paginated_ids:
                return []

            metadata_list = self._fetch_email_metadata(paginated_ids, folder)

            # Sort by date if requested
            metadata_list.sort(
                key=_date_sort_key,
                reverse=(sort_by_date == "desc"),
            )

            # Populate labels if requested
            if include_labels:
                metadata_list = self._populate_labels_for_metadata(metadata_list, folder)

            return metadata_list

        except (FolderNotFoundError, BridgeConnectionError):
            raise
        except Exception as e:
            raise EmailError(f"Failed to list emails: {e}") from e

    def read_mail(self, email_id: str, folder: str = "INBOX") -> Email:
        """
        Read full email content.

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email (default: "INBOX")

        Returns:
            Email object with full content, including labels

        Raises:
            EmailNotFoundError: If email doesn't exist
            FolderNotFoundError: If folder doesn't exist
            BridgeConnectionError: If connection to Bridge fails
            InvalidEmailFormatError: If email cannot be parsed
            ValueError: If email_id is not a valid positive integer
        """
        # Validate email UID format (Priority 2 fix)
        try:
            validate_email_uid(email_id)
        except ValueError as e:
            raise InvalidEmailFormatError(str(e)) from e

        try:
            # Select folder
            self._select_folder(folder)

            # Fetch full email message
            raw_email = self._fetch_email_body(email_id)

            # Fetch FLAGS to determine read status
            flags = self._fetch_email_flags(email_id)
            is_read = "\\Seen" in flags

            # Parse email
            email_obj = self._parse_email(raw_email, email_id, folder, is_read)

            # Get labels for this email and create a new Email with labels populated
            labels = self._get_email_labels(email_id, folder)
            return replace(email_obj, labels=labels)

        except (
            EmailNotFoundError,
            FolderNotFoundError,
            InvalidEmailFormatError,
            BridgeConnectionError,
        ):
            raise
        except Exception as e:
            raise EmailError(f"Failed to read email: {e}") from e

    def get_email_by_message_id(self, message_id: str, folder: str = "INBOX") -> str | None:
        """
        Find an email's UID by its Message-ID header.

        This method is essential for workflows where you need to locate an email
        after sending it. When you send an email using ``send_mail()``, it returns
        a Message-ID header value. However, to read or manipulate that email later,
        you need its UID (the server-assigned identifier). This method bridges that gap.

        **When to use this method:**

        - After sending an email to yourself and waiting for it to arrive
        - When you have a Message-ID from email headers and need to fetch the email
        - For tracking sent emails across folders (e.g., finding in Sent, then in INBOX)

        **Message-ID vs UID:**

        - **Message-ID**: A globally unique identifier set by the sender, stored in
          the email's headers. Format: ``<uuid@domain.com>``. Persists across folders.
        - **UID**: A server-assigned number unique within a specific folder. Can change
          if the mailbox is rebuilt. Required for ``read_mail()`` and ``delete_mail()``.

        Args:
            message_id: The Message-ID header value to search for.
                Can include or exclude angle brackets (e.g., both
                ``<abc@example.com>`` and ``abc@example.com`` work).
            folder: Folder to search in (default: "INBOX")

        Returns:
            Email UID as string if found, None if no matching email exists
            in the specified folder.

        Raises:
            FolderNotFoundError: If the specified folder doesn't exist
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> # Send an email and wait for it to arrive
            >>> message_id = client.send_mail(
            ...     to="myself@proton.me",
            ...     subject="Test",
            ...     body="Hello"
            ... )
            >>> # Wait for email to arrive (delivery takes a few seconds)
            >>> import time
            >>> time.sleep(10)
            >>> # Find the email by Message-ID
            >>> uid = client.get_email_by_message_id(message_id, folder="INBOX")
            >>> if uid:
            ...     email = client.read_mail(uid, folder="INBOX")
            ...     print(email.subject)
            'Test'
        """
        try:
            return self._find_email_by_message_id(message_id, folder)
        except (FolderNotFoundError, BridgeConnectionError):
            raise
        except Exception:
            # _find_email_by_message_id already returns None on errors
            return None

    def find_emails(
        self,
        folder: str = "INBOX",
        subject: str | None = None,
        sender: str | None = None,
        recipient: str | None = None,
        since: datetime | None = None,
        before: datetime | None = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[EmailMetadata]:
        """
        Search for emails matching specified criteria using IMAP SEARCH.

        This method provides flexible email search capabilities using the server-side
        IMAP SEARCH command. Unlike ``list_mails()`` which fetches all emails and
        filters client-side, this method leverages the IMAP server's native search
        functionality for better performance with large mailboxes.

        **Search Behavior:**

        - All specified criteria are combined with AND logic
        - String searches (subject, sender, recipient) are case-insensitive substring matches
        - Date searches use the email's internal date (when received by server)
        - Results are sorted by date descending (newest first)

        **Performance Note:**

        For simple listing with pagination, prefer ``list_mails()``. Use ``find_emails()``
        when you need to search by specific criteria like subject or sender.

        Args:
            folder: Folder to search in (default: "INBOX")
            subject: Search for emails containing this text in the subject line
            sender: Search for emails from addresses containing this text
            recipient: Search for emails to addresses containing this text
            since: Search for emails received on or after this date
            before: Search for emails received before this date
            unread_only: Only return unread emails (default: False)
            limit: Maximum number of results to return (default: 50)

        Returns:
            List of EmailMetadata objects matching all specified criteria,
            sorted by date descending (newest first).

        Raises:
            FolderNotFoundError: If the specified folder doesn't exist
            BridgeConnectionError: If connection to Bridge fails
            ValueError: If limit <= 0

        Example:
            >>> # Find unread emails from a specific sender
            >>> emails = client.find_emails(
            ...     folder="INBOX",
            ...     sender="boss@company.com",
            ...     unread_only=True,
            ... )
            >>> # Find emails with specific subject from last week
            >>> from datetime import datetime, timedelta
            >>> emails = client.find_emails(
            ...     subject="Weekly Report",
            ...     since=datetime.now() - timedelta(days=7),
            ... )
            >>> # Find emails sent to a specific address
            >>> emails = client.find_emails(
            ...     recipient="support@example.com",
            ...     limit=10,
            ... )
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        # Validate date range (BUG #9 fix)
        if since is not None and before is not None and since >= before:
            raise ValueError(
                f"'since' date ({since.isoformat()}) must be before 'before' date ({before.isoformat()})"
            )

        try:
            # Select folder
            self._select_folder(folder)

            # Build search criteria
            search_criteria = self._build_search_criteria(
                subject=subject,
                sender=sender,
                recipient=recipient,
                since=since,
                before=before,
                unread_only=unread_only,
            )

            # Execute search
            email_ids = self._execute_search(search_criteria)

            if not email_ids:
                return []

            # Sort by most recent first and apply limit
            email_ids = list(reversed(email_ids))[:limit]

            # Fetch metadata for matching emails
            metadata_list = self._fetch_email_metadata(email_ids, folder)

            # Sort by date (descending) to ensure consistent ordering
            metadata_list.sort(key=_date_sort_key, reverse=True)

            return metadata_list

        except (FolderNotFoundError, BridgeConnectionError):
            raise
        except Exception as e:
            raise EmailError(f"Failed to search emails: {e}") from e

    def _build_search_criteria(
        self,
        subject: str | None = None,
        sender: str | None = None,
        recipient: str | None = None,
        since: datetime | None = None,
        before: datetime | None = None,
        unread_only: bool = False,
    ) -> list[str]:
        """
        Build IMAP SEARCH criteria list from search parameters.

        Args:
            subject: Subject text to search for
            sender: Sender address text to search for
            recipient: Recipient address text to search for
            since: Emails received on or after this date
            before: Emails received before this date
            unread_only: Only unread emails

        Returns:
            List of IMAP search criteria strings
        """
        criteria: list[str] = []

        if unread_only:
            criteria.append("UNSEEN")

        if subject:
            # IMAP SUBJECT search is case-insensitive substring match
            # String values must be quoted and escaped for IMAP protocol
            criteria.extend(["SUBJECT", f'"{_escape_imap_string(subject)}"'])

        if sender:
            # IMAP FROM search matches against the From header
            criteria.extend(["FROM", f'"{_escape_imap_string(sender)}"'])

        if recipient:
            # IMAP TO search matches against the To header
            criteria.extend(["TO", f'"{_escape_imap_string(recipient)}"'])

        if since:
            # IMAP SINCE format: DD-Mon-YYYY
            date_str = since.strftime("%d-%b-%Y")
            criteria.extend(["SINCE", date_str])

        if before:
            # IMAP BEFORE format: DD-Mon-YYYY
            date_str = before.strftime("%d-%b-%Y")
            criteria.extend(["BEFORE", date_str])

        # If no criteria specified, search all
        if not criteria:
            criteria.append("ALL")

        return criteria

    def _execute_search(self, criteria: list[str]) -> list[str]:
        """
        Execute IMAP SEARCH with the given criteria.

        Args:
            criteria: List of IMAP search criteria

        Returns:
            List of email UIDs matching the criteria

        Raises:
            EmailError: If search fails
        """

        def _search() -> Any:
            """Execute IMAP SEARCH command."""
            status, data = self._connection_manager.connection.uid("search", *criteria)
            if status != "OK":
                raise EmailError(f"IMAP SEARCH failed with status: {status}")
            return data

        try:
            data = self._connection_manager.execute_with_retry(_search)

            # Parse UIDs from response
            if data and data[0]:
                uid_bytes = data[0]
                uid_str = uid_bytes.decode("utf-8") if isinstance(uid_bytes, bytes) else uid_bytes
                return uid_str.split()
            return []

        except Exception as e:
            raise EmailError(f"Failed to execute search: {e}") from e

    def send_mail(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        body_html: str | None = None,
    ) -> str:
        """
        Send an email via ProtonMail Bridge SMTP.

        Composes and sends an email with optional HTML body, CC, and BCC recipients.

        Args:
            to: Primary recipient(s) - single email or list of emails
            subject: Email subject line
            body: Plain text email body
            cc: Optional CC recipient(s) - single email or list of emails
            bcc: Optional BCC recipient(s) - single email or list of emails
            body_html: Optional HTML body (if provided, email becomes multipart)

        Returns:
            Message-ID of the sent email

        Raises:
            InvalidRecipientError: If any recipient address is invalid
            EmailSendError: If sending fails
            SMTPConnectionError: If connection to Bridge fails
            SMTPAuthenticationError: If SMTP authentication fails

        Example:
            >>> manager.send_mail(
            ...     to="recipient@example.com",
            ...     subject="Test Email",
            ...     body="This is a test message.",
            ...     cc=["cc1@example.com", "cc2@example.com"],
            ... )
            '<unique-message-id@protonmail.com>'
        """
        # Normalize recipients to lists
        to_list = [to] if isinstance(to, str) else to
        cc_list = [cc] if isinstance(cc, str) else (cc or [])
        bcc_list = [bcc] if isinstance(bcc, str) else (bcc or [])

        # Validate recipient addresses
        all_recipients = to_list + cc_list + bcc_list
        if not all_recipients:
            raise InvalidRecipientError(
                recipient="(none)", message="At least one recipient (to/cc/bcc) is required"
            )

        for recipient in all_recipients:
            if not recipient or "@" not in recipient:
                raise InvalidRecipientError(recipient=recipient)

        # Create message
        try:
            msg: MIMEMultipart | MIMEText
            if body_html:
                # Multipart message with plain text and HTML
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(body, "plain"))
                msg.attach(MIMEText(body_html, "html"))
            else:
                # Plain text only
                msg = MIMEText(body, "plain")

            # Set headers
            msg["Subject"] = subject
            msg["From"] = self._smtp_connection_manager.email
            msg["To"] = ", ".join(to_list)
            if cc_list:
                msg["Cc"] = ", ".join(cc_list)
            # Note: BCC is NOT added to headers (that's the point of BCC)

            # Generate and add Message-ID
            message_id = f"<{uuid.uuid4()}@protonmail.com>"
            msg["Message-ID"] = message_id

        except Exception as e:
            raise EmailSendError(f"Failed to compose email: {e}") from e

        # Send email
        def _send() -> None:
            """Execute SMTP send command."""
            try:
                conn = self._smtp_connection_manager.get_connection()
                conn.send_message(msg, to_addrs=all_recipients)
            except Exception as e:
                raise EmailSendError(f"Failed to send email: {e}") from e

        try:
            self._smtp_connection_manager.execute_with_retry(_send)
            return message_id
        except Exception as e:
            if isinstance(e, EmailSendError):
                raise
            raise EmailSendError(f"Failed to send email: {e}") from e

    def delete_mail(
        self,
        email_id: str,
        folder: str = "INBOX",
        permanent: bool = False,
    ) -> None:
        """
        Delete an email by moving it to Trash, optionally permanently.

        **Behavior:**

        - ``permanent=False`` (default): Moves the email to Trash. The email can
          still be recovered from Trash.
        - ``permanent=True``: Copies the email to Trash, removes from source,
          then permanently deletes from Trash. This triggers ProtonMail's
          permanent deletion API.

        If the email is already in Trash:

        - ``permanent=False``: No action (email stays in Trash)
        - ``permanent=True``: Permanently deletes the email from Trash

        **ProtonMail Bridge Note:**

        According to ProtonMail Bridge source code, permanent deletion only
        triggers when expunging from the Trash folder. Simply deleting from
        INBOX/Sent only removes the label - the email remains in "All Mail".

        The correct workflow for permanent deletion is:
        1. COPY email to Trash
        2. Mark \\Deleted + EXPUNGE from source folder (removes label)
        3. Mark \\Deleted + EXPUNGE from Trash (triggers permanent deletion)

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email (default: "INBOX")
            permanent: If True, permanently delete after moving to Trash
                (default: False)

        Raises:
            EmailNotFoundError: If email doesn't exist
            FolderNotFoundError: If folder doesn't exist
            EmailDeleteError: If deletion fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> # Move to Trash (can be recovered)
            >>> manager.delete_mail("12345", folder="INBOX")
            >>> # Permanently delete (gone forever)
            >>> manager.delete_mail("12345", folder="INBOX", permanent=True)
        """
        # Validate email UID format (Priority 2 fix)
        try:
            validate_email_uid(email_id)
        except ValueError as e:
            raise InvalidEmailFormatError(str(e)) from e

        # Check for read-only folders (Issue #6 fix)
        if is_readonly_folder(folder):
            raise EmailDeleteError(
                email_id=email_id,
                message=f"Cannot delete emails from '{folder}' - this is a read-only folder. "
                f"Read-only folders are special views that cannot be modified directly.",
            )

        try:
            if folder == "Trash":
                # Already in Trash
                if permanent:
                    # Permanently delete from Trash
                    self._delete_from_folder(email_id, "Trash", expunge=True)
                # If not permanent, do nothing - email stays in Trash
            else:
                # For both permanent and non-permanent deletion, we need to copy
                # to Trash first to avoid orphaning the email in "All Mail"
                message_id = self._get_message_id(email_id, folder)
                self._copy_to_trash(email_id, folder)

                # Delete from source folder (removes the label/folder association)
                self._delete_from_folder(email_id, folder, expunge=True)

                if permanent and message_id:
                    # Find the email in Trash by Message-ID and permanently delete it
                    # This is what triggers ProtonMail's permanent deletion API
                    trash_uid = self._find_email_by_message_id(message_id, "Trash")
                    if trash_uid:
                        self._delete_from_folder(trash_uid, "Trash", expunge=True)

        except (EmailNotFoundError, FolderNotFoundError, EmailDeleteError, BridgeConnectionError):
            raise
        except Exception as e:
            raise EmailDeleteError(email_id=email_id, message=f"Failed to delete email: {e}") from e

    def move_mail(
        self,
        email_id: str,
        source_folder: str,
        destination_folder: str,
    ) -> None:
        """
        Move an email to a different folder.

        This moves the email from the source folder to the destination folder.
        All labels on the email are preserved during the move.

        **IMPORTANT - Email UID Changes After Move:**

        Due to IMAP protocol design, when an email is moved to a different folder,
        it receives a NEW UID in the destination folder. The original UID is only
        valid in the source folder. If you need to reference the email after moving,
        you must use the new UID from the destination folder or track emails by
        their Message-ID header instead.

        Args:
            email_id: Email unique identifier (UID) in the source folder
            source_folder: Current folder containing the email
            destination_folder: Target folder to move the email to

        Raises:
            EmailNotFoundError: If email doesn't exist in source folder
            FolderNotFoundError: If source or destination folder doesn't exist
            EmailError: If move operation fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> manager.move_mail("12345", "INBOX", "archive")
            >>> # Note: email will have a different UID in "archive" folder
            >>> # Move between custom folders
            >>> manager.move_mail("12345", "projects", "completed")
        """
        # No-op if source and destination are the same
        if source_folder == destination_folder:
            return

        # Validate email UID format (Priority 2 fix)
        try:
            validate_email_uid(email_id)
        except ValueError as e:
            raise InvalidEmailFormatError(str(e)) from e

        # Check for read-only folders (Issue #6 fix)
        if is_readonly_folder(source_folder):
            raise EmailError(
                f"Cannot move emails from '{source_folder}' - this is a read-only folder. "
                f"Read-only folders are special views that cannot be modified directly."
            )

        try:
            # Verify email exists in source folder by selecting and checking
            self._select_folder(source_folder)

            # Translate destination folder name to IMAP path
            if self._folder_manager is not None:
                dest_imap_path = self._folder_manager._to_imap_folder_path(destination_folder)
            else:
                dest_imap_path = destination_folder

            # Verify destination folder exists
            try:
                self._verify_folder_exists(dest_imap_path)
            except Exception as e:
                raise FolderNotFoundError(folder_name=destination_folder) from e

            # Select source folder with write access
            self._select_folder_writable(source_folder)

            # Use IMAP MOVE command to atomically move email
            self._move_to_folder(email_id, dest_imap_path)

        except (EmailNotFoundError, FolderNotFoundError, BridgeConnectionError):
            raise
        except Exception as e:
            raise EmailError(f"Failed to move email: {e}") from e

    def add_label(
        self,
        email_id: str,
        folder: str,
        label_name: str,
    ) -> None:
        """
        Add a label to an email.

        The email remains in its current folder. Multiple labels can be
        applied to the same email. Labels are independent of folders.

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email
            label_name: Name of the label to add

        Raises:
            EmailNotFoundError: If email doesn't exist in the folder
            FolderNotFoundError: If folder doesn't exist
            LabelNotFoundError: If label doesn't exist
            EmailError: If labeling fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> manager.add_label("12345", "INBOX", "Important")
            >>> manager.add_label("12345", "INBOX", "Work")
        """
        # Validate email UID format (Priority 2 fix)
        try:
            validate_email_uid(email_id)
        except ValueError as e:
            raise InvalidEmailFormatError(str(e)) from e

        # Validate label name (BUG #8 fix)
        label_name = label_name.strip()
        if not label_name:
            raise InvalidLabelNameError(label_name, "Label name cannot be empty")

        try:
            # Verify email exists in the folder first (Issue #1 fix)
            self._select_folder(folder)

            # Check email existence by fetching its UID
            def _check_email_exists() -> Any:
                """Verify the email UID exists."""
                status, data = self._imap_connection_manager.connection.uid(
                    "fetch", email_id, "(UID)"
                )
                return not (status != "OK" or not data or data[0] is None)

            email_exists = self._imap_connection_manager.execute_with_retry(_check_email_exists)
            if not email_exists:
                raise EmailNotFoundError(email_id=email_id)

            # Verify label exists
            if self._folder_manager is not None:
                # Check if label exists by looking for Labels/<name>
                label_imap_path = f"Labels/{label_name}"
                try:
                    self._verify_folder_exists(label_imap_path)
                except Exception as e:
                    raise LabelNotFoundError(label_name=label_name) from e
            else:
                label_imap_path = f"Labels/{label_name}"

            # Select folder with write access
            self._select_folder_writable(folder)

            # COPY to label (in Bridge, COPY to label = add label, preserve folder)
            self._copy_to_label(email_id, label_imap_path)

        except (EmailNotFoundError, FolderNotFoundError, LabelNotFoundError, BridgeConnectionError):
            raise
        except Exception as e:
            raise EmailError(f"Failed to add label '{label_name}' to email: {e}") from e

    def remove_label(
        self,
        email_id: str,
        label_name: str,
        folder: str | None = None,
    ) -> None:
        """
        Remove a label from an email.

        The email's folder location remains unchanged. Only the specified
        label is removed; other labels on the email are preserved.

        Args:
            email_id: Email unique identifier (UID) - can be from any folder
            label_name: Name of the label to remove
            folder: Optional folder where the email currently resides. If provided,
                   used to look up the email's Message-ID for cross-folder matching.
                   If not provided, uses the label folder directly.

        Raises:
            InvalidEmailFormatError: If email_id is not a valid UID format
            EmailNotFoundError: If email doesn't have this label
            LabelNotFoundError: If label doesn't exist
            EmailError: If unlabeling fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> manager.remove_label("12345", "Important", folder="INBOX")
        """
        try:
            # Validate email_id format early
            try:
                validate_email_uid(email_id)
            except ValueError as e:
                raise InvalidEmailFormatError(str(e)) from e

            # Build label IMAP path
            label_imap_path = f"Labels/{label_name}"

            # Verify label exists
            try:
                self._verify_folder_exists(label_imap_path)
            except Exception as e:
                raise LabelNotFoundError(label_name=label_name) from e

            # If folder is provided, we need to find the email's UID in the label folder
            # by matching on Message-ID
            if folder is not None:
                # Get Message-ID from the source folder
                message_id = self._get_message_id(email_id, folder)
                if not message_id:
                    raise EmailNotFoundError(email_id=email_id)

                # Find the email's UID in the label folder
                label_uid = self._find_email_by_message_id(
                    message_id, label_imap_path, is_raw_imap_path=True
                )
                if not label_uid:
                    # Email exists but doesn't have this label (BUG #5 fix)
                    raise EmailError(
                        f"Email with ID '{email_id}' does not have label '{label_name}' applied. "
                        f"Cannot remove a label that is not on the email."
                    )

                # Use the label folder UID for deletion
                uid_to_delete = label_uid
            else:
                # Assume email_id is already the UID in the label folder
                uid_to_delete = email_id

            # Select the label folder with write access and delete from it
            # This removes the label from the email without affecting its folder location
            self._delete_from_folder(
                uid_to_delete, label_imap_path, expunge=True, is_raw_imap_path=True
            )

        except (
            InvalidEmailFormatError,
            EmailNotFoundError,
            LabelNotFoundError,
            BridgeConnectionError,
        ):
            raise
        except Exception as e:
            raise EmailError(f"Failed to remove label '{label_name}' from email: {e}") from e

    def _copy_or_move_email(
        self,
        email_id: str,
        dest_imap_path: str,
        operation: str = "copy",
    ) -> None:
        """
        Copy or move an email to a destination folder/label.

        This unified method handles all IMAP COPY and MOVE operations:
        - COPY to folder (in Bridge, effectively moves the email)
        - MOVE to folder (atomic move operation)
        - COPY to label (adds label without moving)

        Args:
            email_id: Email unique identifier (UID)
            dest_imap_path: Full IMAP path of the destination
            operation: IMAP command to use - "copy" or "move"

        Raises:
            EmailNotFoundError: If email doesn't exist
            EmailError: If operation fails
            BridgeConnectionError: If connection fails
        """

        # Verify email exists in currently selected folder (BUG #2 fix)
        def _check_email_exists() -> Any:
            """Verify the email UID exists."""
            status, data = self._imap_connection_manager.connection.uid("fetch", email_id, "(UID)")
            return not (status != "OK" or not data or data[0] is None)

        try:
            email_exists = self._imap_connection_manager.execute_with_retry(_check_email_exists)
            if not email_exists:
                raise EmailNotFoundError(email_id=email_id)
        except EmailNotFoundError:
            raise
        except Exception as e:
            # If we can't check existence, let the operation proceed and fail naturally
            logger.debug("Could not verify email existence before %s: %s", operation, e)

        quoted_path = _quote_folder_name(dest_imap_path)

        def _execute() -> Any:
            """Execute IMAP UID COPY or MOVE command."""
            status, data = self._imap_connection_manager.connection.uid(
                operation, email_id, quoted_path
            )
            if status != "OK":
                raise EmailError(f"Failed to {operation} email: {status}")
            return data

        try:
            self._imap_connection_manager.execute_with_retry(_execute)
        except Exception as e:
            if isinstance(e, EmailError):
                raise
            # Translate IMAP errors to user-friendly messages (Issue #5 fix)
            error_msg = str(e)
            friendly_msg = translate_imap_error(error_msg)
            raise EmailError(
                f"Failed to {operation} email to {dest_imap_path}: {friendly_msg}"
            ) from e

    def _copy_to_folder(self, email_id: str, imap_folder_path: str) -> None:
        """Copy an email to a folder (in Bridge, this moves the email)."""
        self._copy_or_move_email(email_id, imap_folder_path, operation="copy")

    def _move_to_folder(self, email_id: str, imap_folder_path: str) -> None:
        """Move an email to a folder using IMAP MOVE command."""
        self._copy_or_move_email(email_id, imap_folder_path, operation="move")

    def _copy_to_label(self, email_id: str, label_imap_path: str) -> None:
        """Copy an email to a label (adds the label without moving the email)."""
        self._copy_or_move_email(email_id, label_imap_path, operation="copy")

    def _verify_folder_exists(self, imap_folder_path: str) -> None:
        """
        Verify that a folder exists by attempting to SELECT it.

        Args:
            imap_folder_path: Full IMAP path of the folder

        Raises:
            FolderNotFoundError: If folder doesn't exist
            BridgeConnectionError: If connection fails
        """
        quoted_path = _quote_folder_name(imap_folder_path)

        def _check() -> Any:
            """Execute IMAP SELECT command to verify folder exists."""
            status, data = self._imap_connection_manager.connection.select(
                quoted_path, readonly=True
            )
            if status != "OK":
                raise FolderNotFoundError(folder_name=imap_folder_path)
            return data

        try:
            self._imap_connection_manager.execute_with_retry(_check)
        except Exception as e:
            if isinstance(e, FolderNotFoundError):
                raise
            raise BridgeConnectionError(f"Failed to verify folder exists: {e}") from e

    def _get_all_label_names(self) -> list[str]:
        """
        Get all user-created label names.

        Returns:
            List of label names (without "Labels/" prefix)
        """
        from .utils import is_label_folder, strip_label_prefix

        if self._folder_manager is None:
            return []

        try:
            # Fetch all folders including labels
            raw_folders = self._folder_manager._fetch_folders_from_bridge(include_labels=True)

            # Filter for label folders and strip prefix
            labels = []
            for folder in raw_folders:
                if is_label_folder(folder.full_path):
                    label_name = strip_label_prefix(folder.full_path)
                    labels.append(label_name)

            return labels

        except Exception:
            return []

    def _find_labels_for_message_id(self, message_id: str, label_names: list[str]) -> list[str]:
        """
        Find which labels from the given list are applied to a message.

        Searches each label folder for the message by its Message-ID header.
        This centralizes the label lookup logic used by both single-email
        and batch label population methods.

        Note: This method gracefully handles the case where a label is deleted
        during the scan (race condition in parallel operations) by skipping
        labels that no longer exist.

        Args:
            message_id: The Message-ID header value of the email
            label_names: List of label names to check (without "Labels/" prefix)

        Returns:
            List of label names that are applied to the message
        """
        from proton_mail_bridge_client.exceptions import FolderNotFoundError

        found_labels = []
        for label_name in label_names:
            label_imap_path = f"Labels/{label_name}"
            try:
                if self._find_email_by_message_id(
                    message_id, label_imap_path, is_raw_imap_path=True
                ):
                    found_labels.append(label_name)
            except FolderNotFoundError:
                # Label was deleted between listing and selecting (race condition).
                # This is expected when multiple processes modify labels concurrently.
                # Simply skip this label since it no longer exists.
                continue
        return found_labels

    def _get_email_labels(self, email_id: str, folder: str) -> tuple[str, ...]:
        """
        Get all labels applied to a specific email.

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email

        Returns:
            Tuple of label names applied to the email
        """
        # Get the Message-ID of this email
        message_id = self._get_message_id(email_id, folder)
        if not message_id:
            return ()

        # Get all available labels
        all_labels = self._get_all_label_names()
        if not all_labels:
            return ()

        # Find which labels apply to this message
        return tuple(self._find_labels_for_message_id(message_id, all_labels))

    def _populate_labels_for_metadata(
        self, metadata_list: list[EmailMetadata], folder: str
    ) -> list[EmailMetadata]:
        """
        Populate labels for a list of EmailMetadata objects.

        Args:
            metadata_list: List of EmailMetadata to update
            folder: Folder the emails are in

        Returns:
            New list of EmailMetadata with labels populated
        """
        if not metadata_list:
            return metadata_list

        # Get all available labels once (optimization: single fetch for batch)
        all_labels = self._get_all_label_names()
        if not all_labels:
            return metadata_list

        # For each email, get Message-ID and find matching labels
        updated_list = []
        for metadata in metadata_list:
            # Get Message-ID for this email
            message_id = self._get_message_id(metadata.id, folder)
            if not message_id:
                updated_list.append(metadata)
                continue

            # Find which labels apply to this message
            email_labels = self._find_labels_for_message_id(message_id, all_labels)

            # Create updated metadata with labels populated
            updated_list.append(replace(metadata, labels=tuple(email_labels)))

        return updated_list

    def _select_folder_internal(
        self,
        folder: str,
        readonly: bool = True,
        *,
        is_raw_imap_path: bool = False,
    ) -> None:
        """
        Unified folder selection with configurable options.

        Args:
            folder: Folder name (user-facing) or raw IMAP path
            readonly: If True, open folder in read-only mode (default: True)
            is_raw_imap_path: If True, folder is already a raw IMAP path
                (e.g., 'Labels/todo'). If False, translates user-facing
                names to IMAP paths.

        Raises:
            FolderNotFoundError: If folder doesn't exist
            BridgeConnectionError: If connection fails
        """
        # Determine the IMAP path to use
        if is_raw_imap_path:
            imap_folder = folder
        elif self._folder_manager is not None:
            imap_folder = self._folder_manager._to_imap_folder_path(folder)
        else:
            imap_folder = folder

        quoted_folder = _quote_folder_name(imap_folder)

        def _select() -> Any:
            """Execute IMAP SELECT command."""
            status, data = self._connection_manager.connection.select(
                quoted_folder, readonly=readonly
            )
            if status != "OK":
                raise FolderNotFoundError(folder_name=folder)
            return data

        try:
            self._connection_manager.execute_with_retry(_select)
        except Exception as e:
            if isinstance(e, FolderNotFoundError):
                raise
            raise BridgeConnectionError(f"Failed to select folder '{folder}': {e}") from e

    def _select_folder(self, folder: str) -> None:
        """Select a folder for read operations (user-facing name)."""
        self._select_folder_internal(folder, readonly=True, is_raw_imap_path=False)

    def _select_folder_raw(self, imap_folder_path: str) -> None:
        """Select a folder for read operations (raw IMAP path)."""
        self._select_folder_internal(imap_folder_path, readonly=True, is_raw_imap_path=True)

    def _select_folder_writable(self, folder: str) -> None:
        """Select a folder for write operations (user-facing name)."""
        self._select_folder_internal(folder, readonly=False, is_raw_imap_path=False)

    def _select_folder_writable_raw(self, imap_folder_path: str) -> None:
        """Select a folder for write operations (raw IMAP path)."""
        self._select_folder_internal(imap_folder_path, readonly=False, is_raw_imap_path=True)

    def _copy_to_trash(self, email_id: str, folder: str) -> None:
        """
        Copy an email to Trash folder.

        Args:
            email_id: Email unique identifier (UID)
            folder: Source folder containing the email

        Raises:
            EmailNotFoundError: If email doesn't exist
            EmailDeleteError: If copy fails
            BridgeConnectionError: If connection fails
        """
        self._select_folder_writable(folder)

        def _copy() -> Any:
            """Execute IMAP UID COPY command."""
            status, data = self._imap_connection_manager.connection.uid("copy", email_id, "Trash")
            if status != "OK":
                raise EmailDeleteError(
                    email_id=email_id,
                    message=f"Failed to copy email to Trash: {status}",
                )
            return data

        try:
            self._imap_connection_manager.execute_with_retry(_copy)
        except Exception as e:
            if isinstance(e, EmailDeleteError):
                raise
            raise EmailDeleteError(
                email_id=email_id, message=f"Failed to copy email to Trash: {e}"
            ) from e

    def _delete_from_folder(
        self, email_id: str, folder: str, expunge: bool = True, *, is_raw_imap_path: bool = False
    ) -> None:
        """
        Delete an email from a specific folder (mark as deleted and optionally expunge).

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email
            expunge: If True, execute EXPUNGE after marking deleted
            is_raw_imap_path: If True, folder is already a raw IMAP path (e.g., 'Labels/todo')

        Raises:
            EmailNotFoundError: If email doesn't exist
            EmailDeleteError: If deletion fails
            BridgeConnectionError: If connection fails
        """
        if is_raw_imap_path:
            self._select_folder_writable_raw(folder)
        else:
            self._select_folder_writable(folder)

        # Mark email with \\Deleted flag
        def _mark_deleted() -> Any:
            """Execute IMAP STORE command to mark as deleted."""
            status, data = self._imap_connection_manager.connection.uid(
                "store", email_id, "+FLAGS", "(\\Deleted)"
            )
            if status != "OK":
                raise EmailDeleteError(
                    email_id=email_id,
                    message=f"Failed to mark email as deleted: {status}",
                )
            # IMAP returns OK with [None] for non-existent UIDs
            if data == [None] or not data:
                raise EmailNotFoundError(email_id=email_id)
            return data

        try:
            self._imap_connection_manager.execute_with_retry(_mark_deleted)
        except (EmailDeleteError, EmailNotFoundError):
            raise
        except Exception as e:
            if "UID" in str(e) or "not found" in str(e).lower():
                raise EmailNotFoundError(email_id=email_id) from e
            raise EmailDeleteError(
                email_id=email_id, message=f"Failed to mark email as deleted: {e}"
            ) from e

        # Expunge to permanently remove if requested
        if expunge:

            def _expunge() -> Any:
                """Execute IMAP EXPUNGE command."""
                status, data = self._imap_connection_manager.connection.expunge()
                if status != "OK":
                    raise EmailDeleteError(
                        email_id=email_id,
                        message=f"Failed to expunge deleted emails: {status}",
                    )
                return data

            try:
                self._imap_connection_manager.execute_with_retry(_expunge)
            except Exception as e:
                raise EmailDeleteError(
                    email_id=email_id, message=f"Failed to expunge deleted emails: {e}"
                ) from e

    def _get_message_id(self, email_id: str, folder: str) -> str | None:
        """
        Get the Message-ID header of an email.

        Args:
            email_id: Email UID
            folder: Folder containing the email

        Returns:
            Message-ID string or None if not found
        """
        self._select_folder(folder)

        def _fetch_message_id() -> Any:
            """Fetch Message-ID header."""
            status, data = self._imap_connection_manager.connection.uid(
                "fetch", email_id, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"
            )
            if status != "OK":
                return None
            return data

        try:
            data = self._imap_connection_manager.execute_with_retry(_fetch_message_id)
            if data and data[0]:
                # Parse Message-ID from response
                # Format: (b'123 (BODY[HEADER.FIELDS (MESSAGE-ID)] {nn}', b'Message-ID: <...>\r\n')
                for item in data:
                    if isinstance(item, tuple) and len(item) >= 2:
                        header_data = item[1]
                        if isinstance(header_data, bytes):
                            header_str = header_data.decode("utf-8", errors="replace")
                            # Extract Message-ID value
                            if "Message-ID:" in header_str or "Message-Id:" in header_str:
                                match = re.search(r"Message-I[dD]:\s*(<[^>]+>|[^\s]+)", header_str)
                                if match:
                                    return match.group(1).strip()
            return None
        except Exception:
            return None

    def _find_email_by_message_id(
        self, message_id: str, folder: str, *, is_raw_imap_path: bool = False
    ) -> str | None:
        """
        Find an email in a folder by its Message-ID header.

        Args:
            message_id: Message-ID header value
            folder: Folder to search in
            is_raw_imap_path: If True, folder is already a raw IMAP path (e.g., 'Labels/todo')

        Returns:
            Email UID if found, None otherwise
        """
        if is_raw_imap_path:
            self._select_folder_raw(folder)
        else:
            self._select_folder(folder)

        def _search_by_message_id() -> Any:
            """Search for email by Message-ID header."""
            # IMAP SEARCH HEADER command
            status, data = self._imap_connection_manager.connection.uid(
                "search", "HEADER", "Message-ID", message_id
            )
            if status != "OK":
                return None
            return data

        try:
            data = self._imap_connection_manager.execute_with_retry(_search_by_message_id)
            if data and data[0]:
                uid_bytes = data[0]
                uid_str = uid_bytes.decode("utf-8") if isinstance(uid_bytes, bytes) else uid_bytes
                uids = uid_str.split()
                if uids:
                    # Return the first matching UID
                    return uids[0]
            return None
        except Exception:
            return None

    def _search_emails(self, unread_only: bool) -> list[str]:
        """
        Search for emails using IMAP SEARCH.

        Args:
            unread_only: If True, only return unread emails

        Returns:
            List of email UIDs as strings

        Raises:
            EmailError: If search fails
        """

        def _search() -> Any:
            """Execute IMAP SEARCH command."""
            search_criteria = "UNSEEN" if unread_only else "ALL"
            status, data = self._connection_manager.connection.uid("search", search_criteria)
            if status != "OK":
                raise EmailError(f"IMAP SEARCH failed with status: {status}")
            return data

        try:
            data = self._connection_manager.execute_with_retry(_search)

            # Parse UIDs from response
            if data and data[0]:
                uid_bytes = data[0]
                uid_str = uid_bytes.decode("utf-8") if isinstance(uid_bytes, bytes) else uid_bytes
                uids = uid_str.split()
                return uids
            return []

        except Exception as e:
            raise EmailError(f"Failed to search emails: {e}") from e

    def _fetch_email_metadata(self, email_ids: list[str], folder: str) -> list[EmailMetadata]:
        """
        Fetch metadata for multiple emails.

        Args:
            email_ids: List of email UIDs
            folder: Current folder name

        Returns:
            List of EmailMetadata objects

        Raises:
            EmailError: If fetch fails
        """
        if not email_ids:
            return []

        def _fetch() -> Any:
            """Execute IMAP UID FETCH command."""
            uid_set = ",".join(email_ids)
            status, data = self._connection_manager.connection.uid(
                "fetch", uid_set, "(UID ENVELOPE FLAGS)"
            )
            if status != "OK":
                raise EmailError(f"IMAP FETCH failed with status: {status}")
            return data

        try:
            data = self._connection_manager.execute_with_retry(_fetch)

            metadata_list = []
            for item in data:
                if not item or item == b")":
                    continue

                try:
                    metadata = self._parse_email_metadata(item, folder)
                    if metadata:
                        metadata_list.append(metadata)
                except Exception:  # nosec B112 - resilience: skip malformed emails, don't crash
                    # Skip individual emails that fail to parse
                    continue

            return metadata_list

        except Exception as e:
            raise EmailError(f"Failed to fetch email metadata: {e}") from e

    def _parse_email_metadata(self, fetch_response: bytes, folder: str) -> EmailMetadata | None:
        """
        Parse IMAP FETCH response into EmailMetadata.

        Args:
            fetch_response: Raw IMAP FETCH response
            folder: Folder name

        Returns:
            EmailMetadata object or None if parsing fails
        """
        try:
            # Parse the fetch response
            # Format: b'1 (UID 123 ENVELOPE (...) FLAGS (\\Seen))'
            response_str = safe_decode_bytes(fetch_response)

            # Extract UID
            uid_match = re.search(r"UID\s+(\d+)", response_str)
            if not uid_match:
                return None
            uid = uid_match.group(1)

            # Extract FLAGS
            flags_match = re.search(r"FLAGS\s+\(([^)]*)\)", response_str)
            flags = flags_match.group(1) if flags_match else ""
            is_read = "\\Seen" in flags

            # Extract ENVELOPE
            # ENVELOPE format: (date subject from sender reply-to to cc bcc in-reply-to message-id)
            envelope_match = re.search(r"ENVELOPE\s+(\(.+\))\s+FLAGS", response_str, re.DOTALL)
            if not envelope_match:
                return None

            envelope_str = envelope_match.group(1)

            # Parse ENVELOPE using utility function
            envelope = parse_imap_envelope(envelope_str)

            # Extract fields and decode as needed
            subject_raw = envelope.get("subject") or ""
            subject = decode_header(subject_raw) if subject_raw else ""
            sender = envelope.get("from") or ""
            recipient = envelope.get("to") or ""
            date_str = envelope.get("date")
            date = parse_email_date(date_str) if date_str else None

            # Create metadata with parsed information
            metadata = EmailMetadata(
                id=uid,
                subject=subject,
                sender=sender,
                recipient=recipient,
                date=date,
                is_read=is_read,
                folder=folder,
            )

            return metadata

        except Exception:
            return None

    def _fetch_email_body(self, email_id: str) -> bytes:
        """
        Fetch full email body.

        Args:
            email_id: Email UID

        Returns:
            Raw email message as bytes

        Raises:
            EmailNotFoundError: If email doesn't exist
            EmailError: If fetch fails
        """

        def _fetch() -> Any:
            """Execute IMAP UID FETCH command."""
            status, data = self._connection_manager.connection.uid(
                "fetch", email_id, "(BODY.PEEK[])"
            )
            if status != "OK":
                raise EmailError(f"IMAP FETCH failed with status: {status}")
            return data

        try:
            data = self._connection_manager.execute_with_retry(_fetch)

            # Extract email body from response
            if data and len(data) > 0:
                # Response format: [(b'1 (UID 123 BODY[] {size}', b'<email content>'), b')']
                for item in data:
                    if isinstance(item, tuple) and len(item) >= 2:
                        body = item[1]
                        if isinstance(body, bytes):
                            return body

            raise EmailNotFoundError(email_id=email_id)

        except Exception as e:
            if isinstance(e, EmailNotFoundError):
                raise
            raise EmailError(f"Failed to fetch email body: {e}") from e

    def _fetch_email_flags(self, email_id: str) -> str:
        """
        Fetch FLAGS for a specific email.

        Args:
            email_id: Email UID

        Returns:
            FLAGS string (e.g., "\\Seen \\Flagged")

        Raises:
            EmailNotFoundError: If email doesn't exist
            EmailError: If fetch fails
        """

        def _fetch() -> Any:
            """Execute IMAP UID FETCH command for FLAGS."""
            status, data = self._connection_manager.connection.uid("fetch", email_id, "(FLAGS)")
            if status != "OK":
                raise EmailError(f"IMAP FETCH FLAGS failed with status: {status}")
            return data

        try:
            data = self._connection_manager.execute_with_retry(_fetch)

            # Extract FLAGS from response
            # Response format: [b'1 (UID 123 FLAGS (\\Seen \\Flagged))']
            if data and len(data) > 0:
                for item in data:
                    if isinstance(item, bytes):
                        response_str = safe_decode_bytes(item)
                        # Extract FLAGS using regex
                        flags_match = re.search(r"FLAGS\s+\(([^)]*)\)", response_str)
                        if flags_match:
                            return flags_match.group(1)

            raise EmailNotFoundError(email_id=email_id)

        except Exception as e:
            if isinstance(e, EmailNotFoundError):
                raise
            raise EmailError(f"Failed to fetch email flags: {e}") from e

    def _parse_email(self, raw_email: bytes, email_id: str, folder: str, is_read: bool) -> Email:
        """
        Parse raw email message into Email object.

        Args:
            raw_email: Raw email message bytes
            email_id: Email UID
            folder: Folder name
            is_read: Whether the email has been read (from IMAP FLAGS)

        Returns:
            Email object with full content

        Raises:
            InvalidEmailFormatError: If email cannot be parsed
        """
        try:
            # Parse email using Python's email library
            msg = email.message_from_bytes(raw_email, policy=email.policy.default)

            # Extract headers
            subject = decode_header(msg.get("Subject", ""))
            sender = msg.get("From", "")
            date_str = msg.get("Date", "")
            date = parse_email_date(date_str) if date_str else None

            # Extract recipients
            to_header = msg.get("To", "")
            cc_header = msg.get("Cc", "")
            bcc_header = msg.get("Bcc", "")

            recipients = parse_address_list(to_header) if to_header else []
            cc = parse_address_list(cc_header) if cc_header else []
            bcc = parse_address_list(bcc_header) if bcc_header else []

            # Extract body parts
            body_plain = None
            body_html = None

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain" and body_plain is None:
                        body_plain = part.get_content()
                    elif content_type == "text/html" and body_html is None:
                        body_html = part.get_content()
            else:
                content_type = msg.get_content_type()
                content = msg.get_content()
                if content_type == "text/plain":
                    body_plain = content
                elif content_type == "text/html":
                    body_html = content

            # Consolidate body: use plain text if available, otherwise convert HTML to text
            if body_plain:
                body = body_plain
            elif body_html:
                body = _html_to_text(body_html)
            else:
                body = ""

            # Get all headers as dict
            headers = dict(msg.items())

            # Create Email object
            email_obj = Email(
                id=email_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                date=date,
                body=body,
                headers=headers,
                is_read=is_read,
                folder=folder,
            )

            return email_obj

        except Exception as e:
            raise InvalidEmailFormatError(
                message=f"Failed to parse email: {e}", email_id=email_id
            ) from e
