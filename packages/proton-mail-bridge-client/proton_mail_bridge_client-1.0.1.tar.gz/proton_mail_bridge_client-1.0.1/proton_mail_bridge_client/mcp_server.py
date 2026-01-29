"""
MCP (Model Context Protocol) server for ProtonMail Bridge Client.

This module provides an MCP server that exposes all ProtonMailClient functionality
as MCP tools. It can be run standalone via `proton-mail-bridge-mcp` command or
as a Python module.

The server uses a lifespan-managed connection to the ProtonMail Bridge,
maintaining a single connection across all tool calls for efficiency.

Environment Variables:
    PROTONMAIL_BRIDGE_EMAIL: Email address for authentication
    PROTONMAIL_BRIDGE_PASSWORD: Password for authentication
    PROTONMAIL_BRIDGE_HOST: IMAP host (default: 127.0.0.1)
    PROTONMAIL_BRIDGE_PORT: IMAP port (default: 1143)
    PROTONMAIL_BRIDGE_SMTP_HOST: SMTP host (default: 127.0.0.1)
    PROTONMAIL_BRIDGE_SMTP_PORT: SMTP port (default: 1025)

Example uvx configuration:
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
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from proton_mail_bridge_client import ProtonMailClient
from proton_mail_bridge_client.models import Email, EmailMetadata, Folder


@dataclass
class AppContext:
    """Application context holding the ProtonMail client connection."""

    client: ProtonMailClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage the ProtonMail Bridge connection lifecycle.

    Creates a single connection when the server starts and closes it
    when the server shuts down. All tools share this connection.
    """
    client = ProtonMailClient()
    client.__enter__()
    try:
        yield AppContext(client=client)
    finally:
        client.__exit__(None, None, None)


# Create MCP server with lifespan
mcp = FastMCP("proton-mail-bridge-mcp", lifespan=app_lifespan)


def _serialize_datetime(obj: Any) -> Any:
    """Convert datetime objects to ISO 8601 strings recursively."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize_datetime(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_datetime(item) for item in obj]
    return obj


def _serialize_folder(folder: Folder) -> dict[str, Any]:
    """Convert Folder dataclass to serializable dict.

    Note: Excludes 'full_path' from serialization as it exposes internal IMAP paths.
    Users should only see and use the 'name' field, which is the user-facing folder name.
    """
    result = asdict(folder)
    # Remove full_path to avoid confusion (BUG #3 fix)
    # Users should use 'name' for all operations, not 'full_path'
    result.pop("full_path", None)
    return result


def _serialize_email_metadata(email: EmailMetadata) -> dict[str, Any]:
    """Convert EmailMetadata dataclass to serializable dict."""
    result = _serialize_datetime(asdict(email))
    return dict(result) if isinstance(result, dict) else {}


def _serialize_email(email: Email) -> dict[str, Any]:
    """Convert Email dataclass to serializable dict."""
    result = _serialize_datetime(asdict(email))
    return dict(result) if isinstance(result, dict) else {}


# =============================================================================
# Helper to get client from context
# =============================================================================


def _get_client(ctx: Context) -> ProtonMailClient:
    """Get the ProtonMailClient from the request context."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    return app_ctx.client


# =============================================================================
# Folder Tools
# =============================================================================


@mcp.tool()
def proton_list_folders(ctx: Context) -> dict[str, Any]:
    """
    List all mail folders in the ProtonMail account.

    Returns:
        A dict with 'folders' containing a list of folder objects, each with:
        - name: Display name (e.g., "INBOX")
        - full_path: Full IMAP path
        - is_system: True for system folders (INBOX, Sent, Trash, etc.)
        - message_count: Number of messages (may be None)
    """
    try:
        client = _get_client(ctx)
        folders = client.list_folders()
        return {"folders": [_serialize_folder(f) for f in folders]}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_create_folder(ctx: Context, name: str) -> dict[str, Any]:
    """
    Create a new mail folder.

    This operation is idempotent - if the folder already exists, it returns
    the existing folder without error.

    Args:
        name: Name for the new folder. Supports nested paths with '/'
              (e.g., "Projects/Work" creates nested folders).

    Returns:
        A dict with 'folder' containing the created/existing folder object.
    """
    try:
        client = _get_client(ctx)
        folder = client.create_folder(name)
        return {"folder": _serialize_folder(folder)}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_rename_folder(ctx: Context, old_name: str, new_name: str) -> dict[str, Any]:
    """
    Rename an existing folder.

    Args:
        old_name: Current name of the folder to rename.
        new_name: New name for the folder.

    Returns:
        A dict with 'folder' containing the renamed folder object.
    """
    try:
        client = _get_client(ctx)
        folder = client.rename_folder(old_name, new_name)
        return {"folder": _serialize_folder(folder)}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_delete_folder(ctx: Context, name: str) -> dict[str, Any]:
    """
    Delete a folder and all its contents.

    Warning: This permanently deletes the folder and all emails within it.
    System folders (INBOX, Sent, Trash, etc.) cannot be deleted.

    Args:
        name: Name of the folder to delete.

    Returns:
        A dict with 'success': True if deleted successfully.
    """
    try:
        client = _get_client(ctx)
        client.delete_folder(name)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_folder_exists(ctx: Context, name: str) -> dict[str, Any]:
    """
    Check if a folder exists.

    Args:
        name: Name of the folder to check.

    Returns:
        A dict with 'exists': True if folder exists, False otherwise.
    """
    try:
        client = _get_client(ctx)
        exists = client.folder_exists(name)
        return {"exists": exists}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


# =============================================================================
# Label Tools
# =============================================================================


@mcp.tool()
def proton_list_labels(ctx: Context) -> dict[str, Any]:
    """
    List all user-created labels.

    Labels are different from folders in ProtonMail - they can be applied
    to emails without moving them.

    Returns:
        A dict with 'labels' containing a list of label names.
    """
    try:
        client = _get_client(ctx)
        labels = client.list_labels()
        return {"labels": labels}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_create_label(ctx: Context, name: str) -> dict[str, Any]:
    """
    Create a new label.

    This operation is idempotent - if the label already exists, it returns
    success without error.

    Args:
        name: Name for the new label. Must not contain '/'.

    Returns:
        A dict with 'label' containing the created label name.
    """
    try:
        client = _get_client(ctx)
        label = client.create_label(name)
        return {"label": label}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_rename_label(ctx: Context, old_name: str, new_name: str) -> dict[str, Any]:
    """
    Rename an existing label.

    Args:
        old_name: Current name of the label to rename.
        new_name: New name for the label.

    Returns:
        A dict with 'label' containing the new label name.
    """
    try:
        client = _get_client(ctx)
        label = client.rename_label(old_name, new_name)
        return {"label": label}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_delete_label(ctx: Context, name: str) -> dict[str, Any]:
    """
    Delete a label.

    This removes the label from all emails that have it applied.
    The emails themselves are not deleted.

    Args:
        name: Name of the label to delete.

    Returns:
        A dict with 'success': True if deleted successfully.
    """
    try:
        client = _get_client(ctx)
        client.delete_label(name)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_label_exists(ctx: Context, name: str) -> dict[str, Any]:
    """
    Check if a label exists.

    Args:
        name: Name of the label to check.

    Returns:
        A dict with 'exists': True if label exists, False otherwise.
    """
    try:
        client = _get_client(ctx)
        exists = client.label_exists(name)
        return {"exists": exists}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


# =============================================================================
# Email Tools
# =============================================================================


@mcp.tool()
def proton_list_mails(
    ctx: Context,
    folder: str = "INBOX",
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    sort_by_date: str = "desc",
    include_labels: bool = False,
) -> dict[str, Any]:
    """
    List emails in a folder with pagination and filtering.

    Args:
        folder: Folder to list emails from (default: "INBOX").
        limit: Maximum number of emails to return (default: 50).
        offset: Number of emails to skip for pagination (default: 0).
        unread_only: If True, only return unread emails (default: False).
        sort_by_date: Sort order - "desc" for newest first, "asc" for oldest first.
        include_labels: If True, include labels for each email (default: False).

    Returns:
        A dict with 'emails' containing a list of email metadata objects.
    """
    try:
        client = _get_client(ctx)
        emails = client.list_mails(
            folder=folder,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            sort_by_date=sort_by_date,
            include_labels=include_labels,
        )
        return {"emails": [_serialize_email_metadata(e) for e in emails]}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_read_mail(ctx: Context, email_id: str, folder: str = "INBOX") -> dict[str, Any]:
    """
    Read the full content of an email.

    Args:
        email_id: The unique ID of the email (from list_mails or find_emails).
        folder: Folder containing the email (default: "INBOX").

    Returns:
        A dict with 'email' containing the full email object including body,
        headers, recipients, and labels.
    """
    try:
        client = _get_client(ctx)
        email = client.read_mail(email_id, folder)
        return {"email": _serialize_email(email)}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_find_emails(
    ctx: Context,
    folder: str = "INBOX",
    subject: str | None = None,
    sender: str | None = None,
    recipient: str | None = None,
    since: str | None = None,
    before: str | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Search for emails using various criteria.

    Uses IMAP SEARCH to find matching emails. All criteria are combined with AND.

    Args:
        folder: Folder to search in (default: "INBOX").
        subject: Search for emails with this text in the subject.
        sender: Search for emails from this sender (email address or name).
        recipient: Search for emails to this recipient.
        since: Search for emails since this date (ISO 8601 format: YYYY-MM-DD).
        before: Search for emails before this date (ISO 8601 format: YYYY-MM-DD).
        unread_only: If True, only return unread emails (default: False).
        limit: Maximum number of emails to return (default: 50).

    Returns:
        A dict with 'emails' containing a list of matching email metadata.
    """
    try:
        # Parse date strings if provided
        since_dt = datetime.fromisoformat(since) if since else None
        before_dt = datetime.fromisoformat(before) if before else None

        client = _get_client(ctx)
        emails = client.find_emails(
            folder=folder,
            subject=subject,
            sender=sender,
            recipient=recipient,
            since=since_dt,
            before=before_dt,
            unread_only=unread_only,
            limit=limit,
        )
        return {"emails": [_serialize_email_metadata(e) for e in emails]}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_get_email_by_message_id(
    ctx: Context, message_id: str, folder: str = "INBOX"
) -> dict[str, Any]:
    """
    Find an email's UID by its Message-ID header.

    This is useful for finding specific emails when you know the Message-ID
    (e.g., from a sent email response).

    Args:
        message_id: The Message-ID header value to search for.
        folder: Folder to search in (default: "INBOX").

    Returns:
        A dict with 'email_id' containing the UID if found, or None if not found.
    """
    try:
        client = _get_client(ctx)
        email_id = client.get_email_by_message_id(message_id, folder)
        return {"email_id": email_id}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_send_mail(
    ctx: Context,
    to: str | list[str],
    subject: str,
    body: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
    body_html: str | None = None,
) -> dict[str, Any]:
    """
    Send an email.

    Args:
        to: Recipient email address(es). Can be a single address or list.
        subject: Email subject line.
        body: Plain text body of the email.
        cc: CC recipient(s) (optional).
        bcc: BCC recipient(s) (optional).
        body_html: HTML version of the body (optional). If provided, sends
                   multipart email with both plain text and HTML.

    Returns:
        A dict with 'message_id' containing the Message-ID of the sent email.
    """
    try:
        client = _get_client(ctx)
        message_id = client.send_mail(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            body_html=body_html,
        )
        return {"message_id": message_id}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_delete_mail(
    ctx: Context, email_id: str, folder: str = "INBOX", permanent: bool = False
) -> dict[str, Any]:
    """
    Delete an email.

    By default, moves the email to Trash. Use permanent=True to permanently
    delete (bypassing Trash).

    Args:
        email_id: The unique ID of the email to delete.
        folder: Folder containing the email (default: "INBOX").
        permanent: If True, permanently delete instead of moving to Trash.

    Returns:
        A dict with 'success': True if deleted successfully.
    """
    try:
        client = _get_client(ctx)
        client.delete_mail(email_id, folder, permanent)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_move_mail(
    ctx: Context, email_id: str, source_folder: str, destination_folder: str
) -> dict[str, Any]:
    """
    Move an email from one folder to another.

    Labels applied to the email are preserved during the move.

    Args:
        email_id: The unique ID of the email to move.
        source_folder: Current folder of the email.
        destination_folder: Folder to move the email to.

    Returns:
        A dict with 'success': True if moved successfully.
    """
    try:
        client = _get_client(ctx)
        client.move_mail(email_id, source_folder, destination_folder)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_add_label_to_email(
    ctx: Context, email_id: str, folder: str, label_name: str
) -> dict[str, Any]:
    """
    Add a label to an email.

    The label must already exist (create it with proton_create_label first).

    Args:
        email_id: The unique ID of the email.
        folder: Folder containing the email.
        label_name: Name of the label to add.

    Returns:
        A dict with 'success': True if label was added successfully.
    """
    try:
        client = _get_client(ctx)
        client.add_label(email_id, folder, label_name)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def proton_remove_label_from_email(
    ctx: Context, email_id: str, label_name: str, folder: str | None = None
) -> dict[str, Any]:
    """
    Remove a label from an email.

    Args:
        email_id: The unique ID of the email.
        label_name: Name of the label to remove.
        folder: Folder containing the email (optional, searches if not provided).

    Returns:
        A dict with 'success': True if label was removed successfully.
    """
    try:
        client = _get_client(ctx)
        client.remove_label(email_id, label_name, folder)
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
