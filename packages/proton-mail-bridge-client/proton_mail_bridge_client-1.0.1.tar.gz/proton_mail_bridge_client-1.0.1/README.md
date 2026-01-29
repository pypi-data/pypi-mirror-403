# ProtonMail Bridge Client

Python library for ProtonMail via Bridge IMAP/SMTP. Zero dependencies (stdlib only).

**Requirements:** Python 3.12-3.14, ProtonMail Bridge running locally

## Installation

```bash
uv add proton-mail-bridge-client
```

## Quick Start

**Interactive Tutorial:** Run `mise run tutorial` for a hands-on Jupyter notebook covering all features (humans only).

```python
from proton_mail_bridge_client import ProtonMailClient

with ProtonMailClient(
    email="your-email@proton.me",
    password="your-bridge-password"  # Bridge password, NOT account password
) as client:
    folders = client.list_folders()
    emails = client.list_mails("INBOX", limit=10)
    if emails:
        email = client.read_mail(email_id=emails[0].id, folder="INBOX")
```

## Configuration

### Environment Variables

```bash
export PROTONMAIL_BRIDGE_EMAIL="your-email@proton.me"
export PROTONMAIL_BRIDGE_PASSWORD="your-bridge-password"
export PROTONMAIL_BRIDGE_HOST="127.0.0.1"  # Default
export PROTONMAIL_BRIDGE_PORT="1143"        # Default
```

Then: `ProtonMailClient()` without parameters.

### SOPS-Encrypted Configuration

For secure credential storage using [SOPS](https://github.com/getsops/sops):

1. Install SOPS: `brew install sops` (macOS) or download from releases
2. Configure encryption (age recommended):
   ```bash
   age-keygen -o ~/.config/sops/age/keys.txt
   export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
   ```
3. Create encrypted config:
   ```bash
   cat > .env << EOF
   PROTONMAIL_BRIDGE_EMAIL=your-email@proton.me
   PROTONMAIL_BRIDGE_PASSWORD=your-bridge-password
   EOF
   sops encrypt .env > .env.sops && rm .env
   ```

**Precedence:** Constructor params > Shell env vars > `.env.sops`

**Behavior:** Silent if `.env.sops` missing or SOPS not installed. Raises `SOPSDecryptionError` if file exists but decryption fails.

### Bridge Setup

1. Install [ProtonMail Bridge](https://proton.me/mail/bridge)
2. Start Bridge before using library
3. Use Bridge-specific password (Bridge settings), NOT account password
4. Default: `127.0.0.1:1143`

---

## MCP Server

The library can also be used as an MCP (Model Context Protocol) server, allowing AI assistants to interact with your ProtonMail account.

### Installation via uvx

```bash
uvx proton-mail-bridge-mcp
```

### Configuration

Add to your MCP client configuration (e.g., Claude Desktop, OpenCode):

```json
{
  "mcpServers": {
    "proton-mail-bridge-mcp": {
      "command": "uvx",
      "args": ["proton-mail-bridge-mcp"],
      "env": {
        "PROTONMAIL_BRIDGE_EMAIL": "your-email@proton.me",
        "PROTONMAIL_BRIDGE_PASSWORD": "your-bridge-password"
      }
    }
  }
}
```

Optional environment variables:
- `PROTONMAIL_BRIDGE_HOST`: IMAP host (default: `127.0.0.1`)
- `PROTONMAIL_BRIDGE_PORT`: IMAP port (default: `1143`)
- `PROTONMAIL_BRIDGE_SMTP_HOST`: SMTP host (default: `127.0.0.1`)
- `PROTONMAIL_BRIDGE_SMTP_PORT`: SMTP port (default: `1025`)

### Available Tools

All 19 public API methods are exposed as MCP tools with the `proton_` prefix:

**Folders:** `proton_list_folders`, `proton_create_folder`, `proton_rename_folder`, `proton_delete_folder`, `proton_folder_exists`

**Labels:** `proton_list_labels`, `proton_create_label`, `proton_rename_label`, `proton_delete_label`, `proton_label_exists`

**Emails:** `proton_list_mails`, `proton_read_mail`, `proton_find_emails`, `proton_get_email_by_message_id`, `proton_send_mail`, `proton_delete_mail`, `proton_move_mail`, `proton_add_label_to_email`, `proton_remove_label_from_email`

Each tool returns a JSON object with either the result data or an error:
```json
{"folders": [...]}       // Success
{"error": "...", "error_type": "FolderNotFoundError"}  // Error
```

---

<!-- LLM-OPTIMIZED API REFERENCE -->
<!-- Format: method(params) -> return | Raises: exceptions | Notes -->

<!-- API_REFERENCE_START -->
## API Reference

### ProtonMailClient

Context manager for IMAP/SMTP operations. Thread-safe with auto-reconnect (3 retries, exponential backoff 1s/2s/4s).

```
ProtonMailClient(email?, password?, host="127.0.0.1", port=1143)
```
Raises `ValueError` if credentials missing from all sources.

### Quick Overview

- [email](#email) - Get the email address used for this client.
- [list_folders](#list_folders) - List all available mail folders.
- [create_folder](#create_folder) - Create a new custom folder, or return existing folder if it already exists.
- [rename_folder](#rename_folder) - Rename an existing custom folder.
- [delete_folder](#delete_folder) - Delete a custom folder.
- [folder_exists](#folder_exists) - Check if a folder exists.
- [list_labels](#list_labels) - List all user-created labels.
- [create_label](#create_label) - Create a new label, or return existing label if it already exists.
- [rename_label](#rename_label) - Rename an existing label.
- [delete_label](#delete_label) - Delete a label.
- [label_exists](#label_exists) - Check if a label exists.
- [list_mails](#list_mails) - List emails in a folder with filtering and pagination.
- [read_mail](#read_mail) - Read full email content.
- [find_emails](#find_emails) - Search for emails matching specified criteria using IMAP SEARCH.
- [get_email_by_message_id](#get_email_by_message_id) - Find an email's UID by its Message-ID header.
- [send_mail](#send_mail) - Send an email via ProtonMail Bridge SMTP.
- [delete_mail](#delete_mail) - Delete an email by moving it to Trash, optionally permanently.
- [move_mail](#move_mail) - Move an email to a different folder.
- [add_label](#add_label) - Add a label to an email.
- [remove_label](#remove_label) - Remove a label from an email.

---

## Methods

### email

Get the email address used for this client.

### list_folders

List all available mail folders.

**Returns:** List of Folder objects

**Raises:**
- `BridgeConnectionError`: If connection to Bridge fails

### create_folder

Create a new custom folder, or return existing folder if it already exists.

This operation is idempotent: calling it multiple times with the same name
is safe and will return the existing folder. The returned folder's name
reflects the actual case as stored on the server.

Supports nested paths: ``"parent/child"`` creates both if needed.
Parent folders are created automatically if they don't exist.

**Args:**
- `name`: Folder name or path (e.g., ``"archive"`` or ``"projects/2026"``)

**Returns:** The created or existing Folder object. If the folder already existed, the returned name reflects the actual case (e.g., requesting ``"Archive"`` when ``"archive"`` exists returns a Folder with ``name="archive"``).

**Raises:**
- `InvalidFolderNameError`: If name is empty or invalid
- `FolderError`: If creation fails
- `BridgeConnectionError`: If connection to Bridge fails

### rename_folder

Rename an existing custom folder.

Can move folders by specifying a new path (e.g., rename ``"foo"`` to ``"bar/foo"``).
Parent folders in ``new_name`` are created automatically if needed.

**Args:**
- `old_name`: Current folder name or path
- `new_name`: New folder name or path

**Returns:** The renamed Folder object

**Raises:**
- `FolderNotFoundError`: If old folder doesn't exist
- `FolderAlreadyExistsError`: If new name already exists
- `InvalidFolderNameError`: If names are invalid or trying to rename system folder
- `FolderError`: If rename fails
- `BridgeConnectionError`: If connection to Bridge fails

### delete_folder

Delete a custom folder.

**Args:**
- `name`: Folder name or path to delete

**Raises:**
- `FolderNotFoundError`: If folder doesn't exist
- `InvalidFolderNameError`: If trying to delete system folder
- `FolderError`: If deletion fails
- `BridgeConnectionError`: If connection to Bridge fails

### folder_exists

Check if a folder exists.

**Args:**
- `name`: Name of the folder to check

**Returns:** True if folder exists, False otherwise

**Raises:**
- `BridgeConnectionError`: If connection to Bridge fails

### list_labels

List all user-created labels.

Returns only labels with clean names (without ``"Labels/"`` prefix).
System folders and custom folders are excluded.

**Returns:** List of label names as strings

**Raises:**
- `BridgeConnectionError`: If connection to Bridge fails
- `LabelError`: If label list cannot be retrieved

### create_label

Create a new label, or return existing label if it already exists.

This operation is idempotent: calling it multiple times with the same name
is safe and will return the existing label name. The returned name
reflects the actual case as stored on the server.

Labels are flat (no hierarchy). Names cannot contain ``"/"``.

**Args:**
- `name`: Label name (cannot contain ``"/"``)

**Returns:** The created or existing label name. If the label already existed, the returned name reflects the actual case (e.g., requesting ``"Important"`` when ``"important"`` exists returns ``"important"``).

**Raises:**
- `InvalidLabelNameError`: If name contains ``"/"`` or is empty
- `LabelError`: If creation fails
- `BridgeConnectionError`: If connection to Bridge fails

### rename_label

Rename an existing label.

Labels are flat (no hierarchy). Names cannot contain ``"/"``.

**Args:**
- `old_name`: Current label name
- `new_name`: New label name (cannot contain ``"/"``)

**Returns:** The new label name

**Raises:**
- `LabelNotFoundError`: If old label doesn't exist
- `LabelAlreadyExistsError`: If new name already exists
- `InvalidLabelNameError`: If names contain ``"/"`` or are empty
- `LabelError`: If rename fails
- `BridgeConnectionError`: If connection to Bridge fails

### delete_label

Delete a label.

**Args:**
- `name`: Label name to delete

**Raises:**
- `LabelNotFoundError`: If label doesn't exist
- `InvalidLabelNameError`: If name is empty or contains ``"/"``
- `LabelError`: If deletion fails
- `BridgeConnectionError`: If connection to Bridge fails

### label_exists

Check if a label exists.

**Args:**
- `name`: Name of the label to check

**Returns:** True if label exists, False otherwise

**Raises:**
- `BridgeConnectionError`: If connection to Bridge fails

### list_mails

List emails in a folder with filtering and pagination.

**Args:**
- `folder`: Folder name (default: "INBOX")
- `limit`: Maximum emails to return (default: 50)
- `offset`: Number of emails to skip (default: 0)
- `unread_only`: Only return unread emails (default: False)
- `sort_by_date`: Sort order - "asc" or "desc" (default: "desc")
- `include_labels`: If True, populate the labels field for each email.
      **Performance Note:** This requires checking each email against
      all label folders, resulting in (N emails x M labels) IMAP queries.
      While ProtonMail Bridge caches data locally, this can still be
      slow for large mailboxes with many labels. Default is False.

**Returns:** List of EmailMetadata objects

**Raises:**
- `FolderNotFoundError`: If folder doesn't exist
- `BridgeConnectionError`: If connection to Bridge fails
- `ValueError`: If limit <= 0 or sort_by_date invalid

### read_mail

Read full email content.

**Args:**
- `email_id`: Email unique identifier (UID)
- `folder`: Folder containing the email (default: "INBOX")

**Returns:** Email object with full content, including all labels applied to the email

**Raises:**
- `InvalidEmailFormatError`: If email_id is not a valid positive integer
- `EmailNotFoundError`: If email doesn't exist
- `FolderNotFoundError`: If folder doesn't exist
- `BridgeConnectionError`: If connection to Bridge fails

### find_emails

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

**Args:**
- `folder`: Folder to search in (default: "INBOX")
- `subject`: Search for emails containing this text in the subject line
- `sender`: Search for emails from addresses containing this text
- `recipient`: Search for emails to addresses containing this text
- `since`: Search for emails received on or after this date
- `before`: Search for emails received before this date
- `unread_only`: Only return unread emails (default: False)
- `limit`: Maximum number of results to return (default: 50)

**Returns:** List of EmailMetadata objects matching all specified criteria, sorted by date descending (newest first).

**Raises:**
- `FolderNotFoundError`: If the specified folder doesn't exist
- `BridgeConnectionError`: If connection to Bridge fails
- `ValueError`: If limit <= 0

### get_email_by_message_id

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

**Args:**
- `message_id`: The Message-ID header value to search for.
      Can include or exclude angle brackets (e.g., both
      ``<abc@example.com>`` and ``abc@example.com`` work).
- `folder`: Folder to search in (default: "INBOX")

**Returns:** Email UID as string if found, None if no matching email exists in the specified folder.

**Raises:**
- `FolderNotFoundError`: If the specified folder doesn't exist
- `BridgeConnectionError`: If connection to Bridge fails

### send_mail

Send an email via ProtonMail Bridge SMTP.

**Args:**
- `to`: Primary recipient(s) - single email or list of emails
- `subject`: Email subject line
- `body`: Plain text email body
- `cc`: Optional CC recipient(s) - single email or list of emails
- `bcc`: Optional BCC recipient(s) - single email or list of emails
- `body_html`: Optional HTML body (if provided, email becomes multipart)

**Returns:** Message-ID of the sent email

**Raises:**
- `InvalidRecipientError`: If any recipient address is invalid
- `EmailSendError`: If sending fails
- `SMTPConnectionError`: If connection to Bridge fails

### delete_mail

Delete an email by moving it to Trash, optionally permanently.

**Behavior:**

- ``permanent=False`` (default): Moves the email to Trash. The email can
still be recovered from Trash.
- ``permanent=True``: Moves the email to Trash, then permanently deletes
it from Trash. The email is gone forever.

If the email is already in Trash:

- ``permanent=False``: No action (email stays in Trash)
- ``permanent=True``: Permanently deletes the email from Trash

**Args:**
- `email_id`: Email unique identifier (UID)
- `folder`: Folder containing the email (default: "INBOX")
- `permanent`: If True, permanently delete after moving to Trash
      (default: False)

**Raises:**
- `InvalidEmailFormatError`: If email_id is not a valid positive integer
- `EmailNotFoundError`: If email doesn't exist
- `FolderNotFoundError`: If folder doesn't exist
- `EmailDeleteError`: If deletion fails
- `BridgeConnectionError`: If connection to Bridge fails

### move_mail

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

**Args:**
- `email_id`: Email unique identifier (UID) in the source folder
- `source_folder`: Current folder containing the email
- `destination_folder`: Target folder to move the email to

**Raises:**
- `InvalidEmailFormatError`: If email_id is not a valid positive integer
- `EmailNotFoundError`: If email doesn't exist in source folder
- `FolderNotFoundError`: If source or destination folder doesn't exist
- `EmailError`: If move operation fails
- `BridgeConnectionError`: If connection to Bridge fails

### add_label

Add a label to an email.

The email remains in its current folder. Multiple labels can be
applied to the same email. Labels are independent of folders.

**Args:**
- `email_id`: Email unique identifier (UID)
- `folder`: Folder containing the email
- `label_name`: Name of the label to add

**Raises:**
- `InvalidEmailFormatError`: If email_id is not a valid positive integer
- `EmailNotFoundError`: If email doesn't exist in the folder
- `FolderNotFoundError`: If folder doesn't exist
- `LabelNotFoundError`: If label doesn't exist
- `EmailError`: If labeling fails
- `BridgeConnectionError`: If connection to Bridge fails

### remove_label

Remove a label from an email.

The email's folder location remains unchanged. Only the specified
label is removed; other labels on the email are preserved.

**Args:**
- `email_id`: Email unique identifier (UID)
- `label_name`: Name of the label to remove
- `folder`: Optional folder where the email currently resides (e.g., "INBOX").
      If provided, the method will find the correct UID in the label folder
      by matching on Message-ID. Recommended for easier usage.

**Raises:**
- `InvalidEmailFormatError`: If email_id is not a valid positive integer
- `EmailNotFoundError`: If email doesn't have this label
- `LabelNotFoundError`: If label doesn't exist
- `EmailError`: If unlabeling fails
- `BridgeConnectionError`: If connection to Bridge fails

---

### Data Models

```python
@dataclass(frozen=True)
class Folder:
    name: str           # Display name ("MyFolder")
    full_path: str      # IMAP path ("Folders/MyFolder")
    is_system: bool     # True for INBOX, Sent, etc.
    message_count: int? # May be None

@dataclass(frozen=True)
class EmailMetadata:
    id: str                    # UID (folder-specific)
    subject: str
    sender: str
    recipient: str             # Primary recipient
    date: datetime             # Timezone-aware
    is_read: bool
    folder: str
    labels: tuple[str, ...]    # Empty unless include_labels=True

@dataclass(frozen=True)
class Email:
    id: str
    subject: str
    sender: str
    recipients: List[str]
    cc: List[str]
    bcc: List[str]
    date: datetime
    body: str                  # Plain text (HTML auto-converted)
    headers: Dict[str, str]
    is_read: bool
    folder: str
    labels: tuple[str, ...]    # Always populated
```

---

### Exception Hierarchy

```
ProtonMailBridgeError
├── BridgeConnectionError
├── BridgeAuthenticationError
├── BridgeTimeoutError
├── ConfigurationError
│   └── SOPSDecryptionError        .file_path: str
├── SMTPConnectionError
├── SMTPAuthenticationError
├── SMTPTimeoutError
├── FolderError
│   ├── FolderNotFoundError        .folder_name: str
│   ├── FolderAlreadyExistsError   .folder_name: str
│   └── InvalidFolderNameError     .folder_name: str
├── EmailError
│   ├── EmailNotFoundError         .email_id: str
│   ├── InvalidEmailFormatError    .email_id: str
│   ├── EmailSendError
│   ├── InvalidRecipientError
│   └── EmailDeleteError
└── LabelError
    ├── LabelNotFoundError         .label_name: str
    ├── LabelAlreadyExistsError    .label_name: str
    └── InvalidLabelNameError
```
---

<!-- API_REFERENCE_END -->
## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Bridge connection failed" | Ensure Bridge running on 127.0.0.1:1143. Check: `lsof -i :1143` |
| "Authentication failed" | Use Bridge password (Bridge settings → Account → Mailbox password), NOT account password |
| "Folder not found" | Case-sensitive. Use `list_folders()` to see exact names |
| "Email not found" | UID from `list_mails()`. Email may have moved/deleted |
| Slow performance | Use pagination (`limit=50`), `unread_only=True` |
| Encoding issues | Library auto-handles. Check `email.headers` for raw info |
| Thread safety | Use one client per thread. Connection uses `RLock` |
| Connection drops | Auto-reconnect with 3 retries. Context manager ensures cleanup |

---

## Version 1.1.0

**Features:** Folders (CRUD, nested), Labels (CRUD), Emails (list/read/send/delete/move/search), Label emails, Find by Message-ID, Persistent connections, Auto-retry, Thread-safe, SOPS config

**Limitations:** No mark read/unread, No attachments, No batch ops

**Roadmap:** Drafts, Mark read/unread, Attachments, Async support

---

## Development

For development setup, testing, code style, and contribution guidelines, see **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## CI/CD Pipeline

For GitLab CI pipeline documentation, runner setup, and SOPS/age credential configuration, see **[PIPELINE.md](PIPELINE.md)**.

## License

This library is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3.0)** - see [LICENSE](LICENSE).

### Attribution Request

While not legally required, we kindly ask that you credit this library in your project's documentation (e.g., README or acknowledgments section) if you find it useful:

> This project uses [ProtonMail Bridge Client](https://gitlab.xarif.de/base/python/proton-mail-bridge-client).
