"""
ProtonMail Bridge Client - Easy-to-use Python library for ProtonMail Bridge

This library provides a simple, intuitive API for interacting with ProtonMail
via the ProtonMail Bridge IMAP interface. Designed for AI agent automation
and email management tasks.

Example:
    >>> from proton_mail_bridge_client import ProtonMailClient
    >>> with ProtonMailClient(email="user@proton.me", password="bridge_pass") as client:
    ...     folders = client.list_folders()
    ...     emails = client.list_mails("INBOX", limit=10)
    ...     email = client.read_mail(email_id="12345")
"""

__version__ = "1.0.0"
__author__ = "ProtonMail Bridge Client Contributors"

# Public API exports
from .client import ProtonMailClient
from .exceptions import (
    BridgeAuthenticationError,
    BridgeConnectionError,
    BridgeTimeoutError,
    ConfigurationError,
    EmailDeleteError,
    EmailError,
    EmailNotFoundError,
    EmailSendError,
    FolderAlreadyExistsError,
    FolderError,
    FolderNotFoundError,
    InvalidEmailFormatError,
    InvalidFolderNameError,
    InvalidLabelNameError,
    InvalidRecipientError,
    LabelAlreadyExistsError,
    LabelError,
    LabelNotFoundError,
    ProtonMailBridgeError,
    SMTPAuthenticationError,
    SMTPConnectionError,
    SMTPTimeoutError,
    SOPSDecryptionError,
)
from .models import Email, EmailMetadata, Folder

__all__ = [
    "BridgeAuthenticationError",
    "BridgeConnectionError",
    "BridgeTimeoutError",
    "ConfigurationError",
    "Email",
    "EmailDeleteError",
    "EmailError",
    "EmailMetadata",
    "EmailNotFoundError",
    "EmailSendError",
    "Folder",
    "FolderAlreadyExistsError",
    "FolderError",
    "FolderNotFoundError",
    "InvalidEmailFormatError",
    "InvalidFolderNameError",
    "InvalidLabelNameError",
    "InvalidRecipientError",
    "LabelAlreadyExistsError",
    "LabelError",
    "LabelNotFoundError",
    "ProtonMailBridgeError",
    "ProtonMailClient",
    "SMTPAuthenticationError",
    "SMTPConnectionError",
    "SMTPTimeoutError",
    "SOPSDecryptionError",
]
