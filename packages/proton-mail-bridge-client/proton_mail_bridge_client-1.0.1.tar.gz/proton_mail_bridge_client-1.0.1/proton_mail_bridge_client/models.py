"""
Data models for proton-mail-bridge-client.

Immutable dataclasses representing folders, emails, and email metadata.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Folder:
    """
    Represents a mail folder (including labels in ProtonMail).

    Attributes:
        name: Display name (e.g., "INBOX", "Sent")
        full_path: Full IMAP path
        is_system: True for system folders (INBOX, Sent, etc.)
        message_count: Total messages in folder (None if not fetched)
    """

    name: str
    full_path: str
    is_system: bool
    message_count: int | None = None


@dataclass(frozen=True)
class EmailMetadata:
    """
    Lightweight email summary for listing operations.

    Contains essential information without full email body, optimized for
    performance when listing many emails.

    Attributes:
        id: IMAP UID (unique within folder)
        subject: Email subject line
        sender: Sender email address with optional name
        recipient: Primary To: recipient
        date: Email date/time
        is_read: Whether email has been read
        folder: Folder containing this email
        labels: Labels applied to this email (empty list if none)
    """

    id: str
    subject: str
    sender: str
    recipient: str
    date: datetime | None
    is_read: bool
    folder: str
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class Email:
    """
    Complete email with full content.

    Contains all email headers, body content, and metadata. Used when
    reading a specific email.

    Attributes:
        id: IMAP UID
        subject: Email subject line
        sender: Sender email address with optional name
        recipients: All To: recipients
        cc: All CC recipients
        bcc: All BCC recipients
        date: Email date/time
        body: Email body as plain text (converted from HTML if necessary)
        headers: All email headers as key-value pairs
        is_read: Whether email has been read
        folder: Folder containing this email
        labels: Labels applied to this email (empty tuple if none)
    """

    id: str
    subject: str
    sender: str
    recipients: list[str]
    cc: list[str]
    bcc: list[str]
    date: datetime | None
    body: str
    headers: dict[str, str]
    is_read: bool
    folder: str
    labels: tuple[str, ...] = ()
