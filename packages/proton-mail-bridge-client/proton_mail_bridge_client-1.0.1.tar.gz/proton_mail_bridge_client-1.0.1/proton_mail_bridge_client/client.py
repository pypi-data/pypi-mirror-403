"""
ProtonMailClient - Main entry point for proton-mail-bridge-client.

Provides a simple, unified API for interacting with ProtonMail via Bridge.
"""

from datetime import datetime

from .config import (
    DEFAULT_IMAP_HOST,
    DEFAULT_IMAP_PORT,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    load_config_from_env,
)
from .connection import IMAPConnectionManager
from .email import EmailManager
from .folder import FolderManager
from .label import LabelManager
from .models import Email, EmailMetadata, Folder
from .smtp_connection import SMTPConnectionManager


class ProtonMailClient:
    """
    Main client for ProtonMail Bridge operations.

    This class provides a simple, unified API for all ProtonMail operations.
    Use as a context manager to ensure proper connection cleanup.

    Example:
        >>> with ProtonMailClient(email="user@proton.me", password="bridge_pass") as client:
        ...     folders = client.list_folders()
        ...     emails = client.list_mails("INBOX", limit=10)
        ...     email = client.read_mail(email_id="12345")
    """

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        host: str = DEFAULT_IMAP_HOST,
        port: int = DEFAULT_IMAP_PORT,
        smtp_host: str = DEFAULT_SMTP_HOST,
        smtp_port: int = DEFAULT_SMTP_PORT,
    ):
        """
        Initialize ProtonMailClient.

        Args:
            email: ProtonMail email address (or set PROTONMAIL_BRIDGE_EMAIL env var)
            password: Bridge password (or set PROTONMAIL_BRIDGE_PASSWORD env var)
            host: Bridge IMAP host (default: 127.0.0.1)
            port: Bridge IMAP port (default: 1143)
            smtp_host: Bridge SMTP host (default: 127.0.0.1)
            smtp_port: Bridge SMTP port (default: 1025)

        Raises:
            ValueError: If credentials are not provided via params or env vars
        """
        # Load config from environment if credentials not provided
        if email is None or password is None:
            config = load_config_from_env()
            if config:
                email = email or config.email
                password = password or config.password

        # Validate credentials
        if not email or not password:
            raise ValueError(
                "Email and password must be provided either as parameters or via "
                "PROTONMAIL_BRIDGE_EMAIL and PROTONMAIL_BRIDGE_PASSWORD environment variables"
            )

        # Store configuration
        self._email = email
        self._password = password
        self._host = host
        self._port = port
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port

        # Initialize managers (connection established in __enter__)
        self._imap_connection_manager: IMAPConnectionManager | None = None
        self._smtp_connection_manager: SMTPConnectionManager | None = None
        self._folder_manager: FolderManager | None = None
        self._email_manager: EmailManager | None = None
        self._label_manager: LabelManager | None = None
        # Backwards compatibility alias
        self._connection_manager: IMAPConnectionManager | None = None

    @property
    def email(self) -> str:
        """Get the email address used for this client."""
        return self._email

    def __enter__(self) -> "ProtonMailClient":
        """Context manager entry - establishes connection."""
        # Create IMAP connection manager
        self._imap_connection_manager = IMAPConnectionManager(
            host=self._host,
            port=self._port,
            email=self._email,
            password=self._password,
        )

        # Create SMTP connection manager
        self._smtp_connection_manager = SMTPConnectionManager(
            host=self._smtp_host,
            port=self._smtp_port,
            email=self._email,
            password=self._password,
        )

        # Establish connections (login is handled within connect())
        self._imap_connection_manager.connect()
        self._smtp_connection_manager.connect()

        # Backwards compatibility alias
        self._connection_manager = self._imap_connection_manager

        # Initialize managers
        self._folder_manager = FolderManager(self._imap_connection_manager)
        self._email_manager = EmailManager(
            self._imap_connection_manager,
            self._smtp_connection_manager,
            self._folder_manager,
        )
        self._label_manager = LabelManager(self._imap_connection_manager, self._folder_manager)

        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        """Context manager exit - closes connection."""
        if self._imap_connection_manager:
            self._imap_connection_manager.disconnect()
        if self._smtp_connection_manager:
            self._smtp_connection_manager.disconnect()

    # =========================================================================
    # Folder Operations
    # =========================================================================

    def list_folders(self) -> list[Folder]:
        """
        List all available mail folders.

        Returns:
            List of Folder objects

        Raises:
            BridgeConnectionError: If connection to Bridge fails
        """
        if not self._folder_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._folder_manager.list_folders()

    def create_folder(self, name: str) -> Folder:
        """
        Create a new custom folder, or return existing folder if it already exists.

        This operation is idempotent: calling it multiple times with the same name
        is safe and will return the existing folder. The returned folder's name
        reflects the actual case as stored on the server.

        Supports nested paths: ``"parent/child"`` creates both if needed.
        Parent folders are created automatically if they don't exist.

        Args:
            name: Folder name or path (e.g., ``"archive"`` or ``"projects/2026"``)

        Returns:
            The created or existing Folder object. If the folder already existed,
            the returned name reflects the actual case (e.g., requesting ``"Archive"``
            when ``"archive"`` exists returns a Folder with ``name="archive"``).

        Raises:
            InvalidFolderNameError: If name is empty or invalid
            FolderError: If creation fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     folder = client.create_folder("projects/2026")
            ...     print(folder.name)
            'projects/2026'
            ...     # Idempotent: calling again returns existing folder
            ...     folder2 = client.create_folder("Projects/2026")
            ...     print(folder2.name)  # Returns actual case
            'projects/2026'
        """
        if not self._folder_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._folder_manager.create_folder(name)

    def rename_folder(self, old_name: str, new_name: str) -> Folder:
        """
        Rename an existing custom folder.

        Can move folders by specifying a new path (e.g., rename ``"foo"`` to ``"bar/foo"``).
        Parent folders in ``new_name`` are created automatically if needed.

        Args:
            old_name: Current folder name or path
            new_name: New folder name or path

        Returns:
            The renamed Folder object

        Raises:
            FolderNotFoundError: If old folder doesn't exist
            FolderAlreadyExistsError: If new name already exists
            InvalidFolderNameError: If names are invalid or trying to rename system folder
            FolderError: If rename fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     folder = client.rename_folder("old_name", "new_name")
            ...     print(folder.name)
            'new_name'
        """
        if not self._folder_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._folder_manager.rename_folder(old_name, new_name)

    def delete_folder(self, name: str) -> None:
        """
        Delete a custom folder.

        Args:
            name: Folder name or path to delete

        Raises:
            FolderNotFoundError: If folder doesn't exist
            InvalidFolderNameError: If trying to delete system folder
            FolderError: If deletion fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     client.delete_folder("old_project")
        """
        if not self._folder_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._folder_manager.delete_folder(name)

    def folder_exists(self, name: str) -> bool:
        """
        Check if a folder exists.

        Args:
            name: Name of the folder to check

        Returns:
            True if folder exists, False otherwise

        Raises:
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     if client.folder_exists("projects"):
            ...         print("Folder exists")
        """
        if not self._folder_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._folder_manager.folder_exists(name)

    # =========================================================================
    # Label Operations
    # =========================================================================

    def list_labels(self) -> list[str]:
        """
        List all user-created labels.

        Returns only labels with clean names (without ``"Labels/"`` prefix).
        System folders and custom folders are excluded.

        Returns:
            List of label names as strings

        Raises:
            BridgeConnectionError: If connection to Bridge fails
            LabelError: If label list cannot be retrieved

        Example:
            >>> with ProtonMailClient() as client:
            ...     labels = client.list_labels()
            ...     for label in labels:
            ...         print(label)
            'important'
            'work'
        """
        if not self._label_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._label_manager.list_labels()

    def create_label(self, name: str) -> str:
        """
        Create a new label, or return existing label if it already exists.

        This operation is idempotent: calling it multiple times with the same name
        is safe and will return the existing label name. The returned name
        reflects the actual case as stored on the server.

        Labels are flat (no hierarchy). Names cannot contain ``"/"``.

        Args:
            name: Label name (cannot contain ``"/"``)

        Returns:
            The created or existing label name. If the label already existed,
            the returned name reflects the actual case (e.g., requesting ``"Important"``
            when ``"important"`` exists returns ``"important"``).

        Raises:
            InvalidLabelNameError: If name contains ``"/"`` or is empty
            LabelError: If creation fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     label = client.create_label("urgent")
            ...     print(label)
            'urgent'
            ...     # Idempotent: calling again returns existing label
            ...     label2 = client.create_label("Urgent")
            ...     print(label2)  # Returns actual case
            'urgent'
        """
        if not self._label_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._label_manager.create_label(name)

    def rename_label(self, old_name: str, new_name: str) -> str:
        """
        Rename an existing label.

        Labels are flat (no hierarchy). Names cannot contain ``"/"``.

        Args:
            old_name: Current label name
            new_name: New label name (cannot contain ``"/"``)

        Returns:
            The new label name

        Raises:
            LabelNotFoundError: If old label doesn't exist
            LabelAlreadyExistsError: If new name already exists
            InvalidLabelNameError: If names contain ``"/"`` or are empty
            LabelError: If rename fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     new_name = client.rename_label("old_label", "new_label")
            ...     print(new_name)
            'new_label'
        """
        if not self._label_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._label_manager.rename_label(old_name, new_name)

    def delete_label(self, name: str) -> None:
        """
        Delete a label.

        Args:
            name: Label name to delete

        Raises:
            LabelNotFoundError: If label doesn't exist
            InvalidLabelNameError: If name is empty or contains ``"/"``
            LabelError: If deletion fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     client.delete_label("old_label")
        """
        if not self._label_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._label_manager.delete_label(name)

    def label_exists(self, name: str) -> bool:
        """
        Check if a label exists.

        Args:
            name: Name of the label to check

        Returns:
            True if label exists, False otherwise

        Raises:
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     if client.label_exists("important"):
            ...         print("Label exists")
        """
        if not self._label_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._label_manager.label_exists(name)

    # =========================================================================
    # Email Operations
    # =========================================================================

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
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.list_mails(
            folder=folder,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            sort_by_date=sort_by_date,
            include_labels=include_labels,
        )

    def read_mail(self, email_id: str, folder: str = "INBOX") -> Email:
        """
        Read full email content.

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email (default: "INBOX")

        Returns:
            Email object with full content, including all labels applied to the email

        Raises:
            InvalidEmailFormatError: If email_id is not a valid positive integer
            EmailNotFoundError: If email doesn't exist
            FolderNotFoundError: If folder doesn't exist
            BridgeConnectionError: If connection to Bridge fails
        """
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.read_mail(email_id=email_id, folder=folder)

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
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.find_emails(
            folder=folder,
            subject=subject,
            sender=sender,
            recipient=recipient,
            since=since,
            before=before,
            unread_only=unread_only,
            limit=limit,
        )

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
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.get_email_by_message_id(message_id=message_id, folder=folder)

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
        """
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.send_mail(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            body_html=body_html,
        )

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
        - ``permanent=True``: Moves the email to Trash, then permanently deletes
          it from Trash. The email is gone forever.

        If the email is already in Trash:

        - ``permanent=False``: No action (email stays in Trash)
        - ``permanent=True``: Permanently deletes the email from Trash

        Args:
            email_id: Email unique identifier (UID)
            folder: Folder containing the email (default: "INBOX")
            permanent: If True, permanently delete after moving to Trash
                (default: False)

        Raises:
            InvalidEmailFormatError: If email_id is not a valid positive integer
            EmailNotFoundError: If email doesn't exist
            FolderNotFoundError: If folder doesn't exist
            EmailDeleteError: If deletion fails
            BridgeConnectionError: If connection to Bridge fails
        """
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.delete_mail(
            email_id=email_id,
            folder=folder,
            permanent=permanent,
        )

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
        you must use the new UID from the destination folder or track the email by
        its Message-ID header instead.

        **ProtonMail Bridge Note:**

        Due to ProtonMail Bridge's design, COPY to a folder actually moves the
        message (removes from source). This behavior is leveraged for correct
        folder moves without needing explicit DELETE+EXPUNGE from source.

        Args:
            email_id: Email unique identifier (UID) in the source folder
            source_folder: Current folder containing the email
            destination_folder: Target folder to move the email to

        Raises:
            InvalidEmailFormatError: If email_id is not a valid positive integer
            EmailNotFoundError: If email doesn't exist in source folder
            FolderNotFoundError: If source or destination folder doesn't exist
            EmailError: If move operation fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     client.move_mail("12345", "INBOX", "archive")
            ...     # Note: email will have a different UID in "archive" folder
            ...     # Move between custom folders
            ...     client.move_mail("12345", "projects", "completed")
        """
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.move_mail(
            email_id=email_id,
            source_folder=source_folder,
            destination_folder=destination_folder,
        )

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
            InvalidEmailFormatError: If email_id is not a valid positive integer
            EmailNotFoundError: If email doesn't exist in the folder
            FolderNotFoundError: If folder doesn't exist
            LabelNotFoundError: If label doesn't exist
            EmailError: If labeling fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     client.add_label("12345", "INBOX", "Important")
            ...     client.add_label("12345", "INBOX", "Work")
        """
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.add_label(
            email_id=email_id,
            folder=folder,
            label_name=label_name,
        )

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
            email_id: Email unique identifier (UID)
            label_name: Name of the label to remove
            folder: Optional folder where the email currently resides (e.g., "INBOX").
                   If provided, the method will find the correct UID in the label folder
                   by matching on Message-ID. Recommended for easier usage.

        Raises:
            InvalidEmailFormatError: If email_id is not a valid positive integer
            EmailNotFoundError: If email doesn't have this label
            LabelNotFoundError: If label doesn't exist
            EmailError: If unlabeling fails
            BridgeConnectionError: If connection to Bridge fails

        Example:
            >>> with ProtonMailClient() as client:
            ...     # Remove label using email's folder (recommended)
            ...     client.remove_label("12345", "Important", folder="INBOX")
        """
        if not self._email_manager:
            raise RuntimeError("Client not connected. Use 'with' statement or call __enter__()")

        return self._email_manager.remove_label(
            email_id=email_id,
            label_name=label_name,
            folder=folder,
        )
