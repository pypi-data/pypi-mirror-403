"""
Exception hierarchy for proton-mail-bridge-client.

All library exceptions inherit from ProtonMailBridgeError to allow users
to catch all library-specific errors with a single except clause.
"""


class ProtonMailBridgeError(Exception):
    """Base exception for all proton-mail-bridge-client errors."""

    pass


class BridgeConnectionError(ProtonMailBridgeError):
    """Raised when connection to ProtonMail Bridge fails or is lost."""

    pass


class BridgeAuthenticationError(ProtonMailBridgeError):
    """Raised when authentication with ProtonMail Bridge fails."""

    pass


class BridgeTimeoutError(ProtonMailBridgeError):
    """Raised when an operation times out."""

    pass


class SMTPConnectionError(ProtonMailBridgeError):
    """Raised when SMTP connection to ProtonMail Bridge fails or is lost."""

    pass


class SMTPAuthenticationError(ProtonMailBridgeError):
    """Raised when SMTP authentication with ProtonMail Bridge fails."""

    pass


class SMTPTimeoutError(ProtonMailBridgeError):
    """Raised when an SMTP operation times out."""

    pass


class FolderError(ProtonMailBridgeError):
    """Base exception for folder-related errors."""

    pass


class FolderNotFoundError(FolderError):
    """Raised when a requested folder does not exist."""

    def __init__(self, folder_name: str, message: str | None = None):
        self.folder_name = folder_name
        default_message = f"Folder '{folder_name}' not found"
        super().__init__(message or default_message)


class FolderAlreadyExistsError(FolderError):
    """Raised when attempting to create a folder that already exists."""

    def __init__(self, folder_name: str, message: str | None = None):
        self.folder_name = folder_name
        default_message = f"Folder '{folder_name}' already exists"
        super().__init__(message or default_message)


class InvalidFolderNameError(FolderError):
    """Raised when a folder name is invalid."""

    def __init__(self, folder_name: str, message: str | None = None):
        self.folder_name = folder_name
        default_message = f"Invalid folder name: '{folder_name}'"
        super().__init__(message or default_message)


class EmailError(ProtonMailBridgeError):
    """Base exception for email-related errors."""

    pass


class EmailNotFoundError(EmailError):
    """Raised when a requested email does not exist."""

    def __init__(self, email_id: str, message: str | None = None):
        self.email_id = email_id
        default_message = f"Email with ID '{email_id}' not found"
        super().__init__(message or default_message)


class InvalidEmailFormatError(EmailError):
    """Raised when an email cannot be parsed."""

    def __init__(self, email_id: str | None = None, message: str | None = None):
        self.email_id = email_id
        default_message = "Invalid email format"
        if email_id:
            default_message += f" for email ID '{email_id}'"
        super().__init__(message or default_message)


class EmailSendError(EmailError):
    """Raised when sending an email fails."""

    pass


class InvalidRecipientError(EmailError):
    """Raised when an email recipient address is invalid."""

    def __init__(self, recipient: str, message: str | None = None):
        self.recipient = recipient
        default_message = f"Invalid recipient address: '{recipient}'"
        super().__init__(message or default_message)


class EmailDeleteError(EmailError):
    """Raised when deleting an email fails."""

    def __init__(self, email_id: str, message: str | None = None):
        self.email_id = email_id
        default_message = f"Failed to delete email with ID '{email_id}'"
        super().__init__(message or default_message)


class LabelError(ProtonMailBridgeError):
    """Base exception for label-related errors."""

    pass


class LabelNotFoundError(LabelError):
    """Raised when a requested label does not exist."""

    def __init__(self, label_name: str, message: str | None = None):
        self.label_name = label_name
        default_message = f"Label '{label_name}' not found"
        super().__init__(message or default_message)


class LabelAlreadyExistsError(LabelError):
    """Raised when attempting to create a label that already exists."""

    def __init__(self, label_name: str, message: str | None = None):
        self.label_name = label_name
        default_message = f"Label '{label_name}' already exists"
        super().__init__(message or default_message)


class InvalidLabelNameError(LabelError):
    """Raised when a label name is invalid (e.g., contains '/')."""

    def __init__(self, label_name: str, message: str | None = None):
        self.label_name = label_name
        default_message = f"Invalid label name: '{label_name}'"
        super().__init__(message or default_message)


class ConfigurationError(ProtonMailBridgeError):
    """Base exception for configuration-related errors."""

    pass


class SOPSDecryptionError(ConfigurationError):
    """Raised when SOPS decryption fails for an existing encrypted file."""

    def __init__(self, file_path: str, message: str | None = None):
        self.file_path = file_path
        default_message = f"Failed to decrypt SOPS file '{file_path}'"
        super().__init__(message or default_message)
