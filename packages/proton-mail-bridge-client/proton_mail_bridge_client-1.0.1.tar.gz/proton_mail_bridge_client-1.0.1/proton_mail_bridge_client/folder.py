"""
Folder management for proton-mail-bridge-client.

Handles listing folders via ProtonMail Bridge.
"""

import re
from typing import Any

from .connection import IMAPConnectionManager
from .exceptions import (
    BridgeConnectionError,
    FolderAlreadyExistsError,
    FolderError,
    FolderNotFoundError,
    InvalidFolderNameError,
)
from .models import Folder
from .utils import (
    is_custom_folder,
    is_label_folder,
    is_system_folder,
    normalize_folder_path,
    parse_imap_list_response,
    split_folder_path,
    strip_folder_prefix,
    validate_folder_name,
)


def _quote_folder_name(folder_name: str) -> str:
    """
    Quote IMAP folder name if it contains special characters.

    According to RFC 3501, folder names containing spaces or special characters
    must be quoted. Python's imaplib doesn't automatically quote folder names,
    so we need to do it manually.

    Args:
        folder_name: The folder name to quote

    Returns:
        Quoted folder name if needed, original name otherwise

    Examples:
        >>> _quote_folder_name("INBOX")
        'INBOX'
        >>> _quote_folder_name("All Mail")
        '"All Mail"'
        >>> _quote_folder_name("Folders/My Folder")
        '"Folders/My Folder"'
    """
    # Check if folder name needs quoting (contains spaces or special chars)
    # Per RFC 3501, these characters require quoting: space, (, ), {, %, *, ", \
    needs_quoting = any(char in folder_name for char in [" ", "(", ")", "{", "%", "*", '"', "\\"])

    if needs_quoting:
        # Escape any existing double quotes and backslashes
        escaped = folder_name.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    return folder_name


class FolderManager:
    """
    Manages folder operations.

    Provides methods for listing folders and checking folder existence.

    Attributes:
        connection_manager: IMAP connection manager instance
    """

    def __init__(
        self,
        connection_manager: IMAPConnectionManager,
    ):
        """
        Initialize FolderManager.

        Args:
            connection_manager: IMAP connection manager for Bridge access
        """
        self._connection_manager = connection_manager

    def list_folders(self) -> list[Folder]:
        """
        List all available mail folders.

        Returns system folders and custom folders (subfolders of "Folders/").
        Custom folder names have the "Folders/" prefix stripped for clean API.

        The internal meta folders "Folders" and "Labels" are excluded from results
        as they are structural containers. Labels (under "Labels/") are also excluded -
        use LabelManager for those.

        Returns:
            List of Folder objects (system folders + custom folders without prefix)

        Raises:
            BridgeConnectionError: If connection to Bridge fails
            FolderError: If folder list cannot be retrieved
        """
        # Fetch folder list from Bridge
        try:
            folders = self._fetch_folders_from_bridge()
            return folders
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise FolderError(f"Failed to list folders: {e}") from e

    def folder_exists(self, folder_name: str) -> bool:
        """
        Check if a folder exists.

        Note: Comparison is case-insensitive because ProtonMail Bridge
        does not allow folders with the same name but different case.

        Args:
            folder_name: Name of the folder to check

        Returns:
            True if folder exists, False otherwise

        Raises:
            BridgeConnectionError: If connection to Bridge fails
        """
        try:
            folders = self.list_folders()
            folder_name_lower = folder_name.lower()
            return any(f.name.lower() == folder_name_lower for f in folders)
        except BridgeConnectionError:
            raise
        except Exception:
            return False

    def _resolve_folder_name(self, folder_name: str) -> str | None:
        """
        Resolve a folder name to its actual name with correct casing.

        ProtonMail Bridge handles folder names case-insensitively, so we need
        to find the actual folder name as stored to use in IMAP operations.

        Args:
            folder_name: The folder name to resolve (case-insensitive)

        Returns:
            The actual folder name with correct casing, or None if not found
        """
        try:
            folders = self.list_folders()
            folder_name_lower = folder_name.lower()
            for folder in folders:
                if folder.name.lower() == folder_name_lower:
                    return folder.name
            return None
        except Exception:
            return None

    def _resolve_path_with_existing_parents(self, folder_path: str) -> str:
        """
        Resolve a folder path, fixing the case of any existing parent folders.

        For a path like "testfolder/NewSubfolder" where "TestFolder" exists,
        this returns "TestFolder/NewSubfolder".

        This is necessary because ProtonMail Bridge treats folder names as
        case-insensitive, so "testfolder" and "TestFolder" refer to the same
        folder. When renaming, we must use the actual case of existing parents.

        Args:
            folder_path: The folder path to resolve

        Returns:
            The folder path with existing parent folders resolved to their
            actual case. Non-existing path components are kept as-is.
        """
        parts = split_folder_path(folder_path)
        if not parts:
            return folder_path

        # Fetch folders once and build a case-insensitive lookup map.
        # This avoids N IMAP LIST+STATUS operations for an N-segment path.
        folders_by_lower_name = {f.name.lower(): f.name for f in self.list_folders()}

        resolved_parts: list[str] = []
        for part in parts:
            # Build the path up to this point
            current_path = "/".join([*resolved_parts, part]) if resolved_parts else part
            current_path_lower = current_path.lower()

            # Try to resolve to actual case using the cached lookup
            if current_path_lower in folders_by_lower_name:
                # Folder exists - use the resolved name's components
                resolved_parts = split_folder_path(folders_by_lower_name[current_path_lower])
            else:
                # Folder doesn't exist - keep the user-provided name
                resolved_parts.append(part)

        return "/".join(resolved_parts)

    def _to_imap_folder_path(self, folder_name: str) -> str:
        """
        Translate a user-facing folder name to the IMAP path expected by the bridge.

        System folders (INBOX, Sent, Trash, etc.) pass through unchanged.
        Custom folders get "Folders/" prefix prepended.

        Args:
            folder_name: The user-facing folder name (e.g., "catchall", "INBOX")

        Returns:
            The IMAP path (e.g., "Folders/catchall", "INBOX")

        Raises:
            FolderNotFoundError: If the folder does not exist
        """
        # System folders pass through unchanged
        if is_system_folder(folder_name):
            return folder_name

        # For custom folders, verify existence and prepend "Folders/"
        if not self.folder_exists(folder_name):
            raise FolderNotFoundError(folder_name=folder_name)

        return f"Folders/{folder_name}"

    def _fetch_folders_from_bridge(self, include_labels: bool = False) -> list[Folder]:
        """
        Fetch folder list from ProtonMail Bridge via IMAP LIST command.

        Args:
            include_labels: If True, include label folders (Labels/*) in results.
                          If False (default), only return system and custom folders.

        Returns:
            List of Folder objects

        Raises:
            BridgeConnectionError: If connection fails
            FolderError: If IMAP LIST command fails
        """

        def _list_folders() -> Any:
            """Execute IMAP LIST command."""
            status, data = self._connection_manager.connection.list()
            if status != "OK":
                raise FolderError(f"IMAP LIST failed with status: {status}")
            return data

        try:
            # Execute LIST command with retry
            data = self._connection_manager.execute_with_retry(_list_folders)

            # Parse IMAP LIST responses
            folders = []
            for item in data:
                if item is None:
                    continue

                # Parse the response line
                parsed = parse_imap_list_response(item)
                if parsed is None:
                    continue

                _flags, _delimiter, folder_name = parsed

                # Skip empty folder names
                if not folder_name:
                    continue

                # Skip internal meta folders
                if folder_name in ("Folders", "Labels"):
                    continue

                # Determine folder type and process accordingly
                is_system = is_system_folder(folder_name)
                is_custom = is_custom_folder(folder_name)
                is_label = is_label_folder(folder_name)

                # Filter based on include_labels flag
                if include_labels:
                    # Include system folders, custom folders, and labels
                    if not (is_system or is_custom or is_label):
                        continue
                else:
                    # Include only system folders and custom folders (not labels)
                    if not (is_system or is_custom):
                        continue

                # For custom folders, strip the "Folders/" prefix
                display_name = strip_folder_prefix(folder_name) if is_custom else folder_name

                # Count messages in folder (using original folder_name for IMAP commands)
                message_count = self._get_folder_message_count(folder_name)

                # Create Folder object with display name
                folder = Folder(
                    name=display_name,
                    full_path=folder_name,  # Keep original path for IMAP operations
                    is_system=is_system,
                    message_count=message_count,
                )
                folders.append(folder)

            return folders

        except BridgeConnectionError:
            raise
        except Exception as e:
            raise FolderError(f"Failed to fetch folders from Bridge: {e}") from e

    def _get_folder_message_count(self, folder_name: str) -> int:
        """
        Get message count for a folder.

        Args:
            folder_name: Name of the folder

        Returns:
            Number of messages in folder, or 0 if count unavailable
        """
        try:
            # Quote folder name if it contains special characters (e.g., "All Mail")
            # Python's imaplib doesn't automatically quote folder names with spaces
            quoted_name = _quote_folder_name(folder_name)

            def _get_status() -> Any:
                """Execute IMAP STATUS command."""
                status, data = self._connection_manager.connection.status(quoted_name, "(MESSAGES)")
                if status != "OK":
                    return 0
                return data

            data = self._connection_manager.execute_with_retry(_get_status)

            # Parse STATUS response: [b'INBOX (MESSAGES 42)']
            if data and len(data) > 0:
                response = data[0]
                if isinstance(response, bytes):
                    response_str = response.decode("utf-8")
                    # Extract number from "INBOX (MESSAGES 42)"
                    match = re.search(r"MESSAGES\s+(\d+)", response_str)
                    if match:
                        return int(match.group(1))

            return 0

        except Exception:
            # If we can't get the count, return 0 rather than failing
            return 0

    def create_folder(self, name: str) -> Folder:
        """
        Create a new custom folder, or return existing folder if it already exists.

        This operation is idempotent: calling it multiple times with the same name
        is safe and will return the existing folder. The returned folder's name
        reflects the actual case as stored on the server.

        Supports nested paths: "parent/child" creates both if needed.
        Parent folders are created automatically if they don't exist.

        Args:
            name: Folder name or path (e.g., "archive" or "projects/2026")

        Returns:
            The created or existing Folder object. If the folder already existed,
            the returned name reflects the actual case (e.g., requesting "Archive"
            when "archive" exists returns a Folder with name="archive").

        Raises:
            InvalidFolderNameError: If name is empty or invalid
            FolderError: If creation fails
        """
        # Normalize and validate the name
        normalized_name = normalize_folder_path(name)
        if not normalized_name:
            raise InvalidFolderNameError(name, "Folder name cannot be empty")

        # Validate folder name for control characters (Issue #3 fix)
        try:
            validate_folder_name(normalized_name)
        except ValueError as e:
            raise InvalidFolderNameError(name, str(e)) from e

        # Check if folder already exists (case-insensitive)
        actual_name = self._resolve_folder_name(normalized_name)
        if actual_name is not None:
            # Return the existing folder with its actual case
            imap_path = f"Folders/{actual_name}"
            message_count = self._get_folder_message_count(imap_path)
            return Folder(
                name=actual_name,
                full_path=imap_path,
                is_system=False,
                message_count=message_count,
            )

        # Ensure parent folders exist (for nested paths)
        self._ensure_parent_folders_exist(normalized_name)

        # Create the folder via IMAP CREATE command
        imap_path = f"Folders/{normalized_name}"
        quoted_path = _quote_folder_name(imap_path)

        def _create_folder() -> Any:
            """Execute IMAP CREATE command."""
            status, data = self._connection_manager.connection.create(quoted_path)
            if status != "OK":
                raise FolderError(f"IMAP CREATE failed with status: {status}, data: {data}")
            return data

        try:
            self._connection_manager.execute_with_retry(_create_folder)

            # Return the created folder
            message_count = self._get_folder_message_count(imap_path)
            return Folder(
                name=normalized_name,
                full_path=imap_path,
                is_system=False,
                message_count=message_count,
            )

        except BridgeConnectionError:
            raise
        except FolderError:
            raise
        except Exception as e:
            raise FolderError(f"Failed to create folder '{normalized_name}': {e}") from e

    def rename_folder(self, old_name: str, new_name: str) -> Folder:
        """
        Rename an existing custom folder.

        Can move folders by specifying a new path (e.g., rename "foo" to "bar/foo").
        Parent folders in new_name are created automatically if needed.

        Note: Folder lookup is case-insensitive. If you pass "MyFolder" but the
        actual folder is named "myfolder", it will still be found and renamed.

        Args:
            old_name: Current folder name or path (case-insensitive)
            new_name: New folder name or path

        Returns:
            The renamed Folder object

        Raises:
            FolderNotFoundError: If old folder doesn't exist
            FolderAlreadyExistsError: If new name already exists
            InvalidFolderNameError: If names are invalid or trying to rename system folder
            FolderError: If rename fails
        """
        # Normalize and validate names
        normalized_old = normalize_folder_path(old_name)
        normalized_new = normalize_folder_path(new_name)

        if not normalized_old:
            raise InvalidFolderNameError(old_name, "Old folder name cannot be empty")
        if not normalized_new:
            raise InvalidFolderNameError(new_name, "New folder name cannot be empty")

        # Validate folder names for control characters (Issue #3 fix)
        try:
            validate_folder_name(normalized_new)
        except ValueError as e:
            raise InvalidFolderNameError(new_name, str(e)) from e

        # Cannot rename system folders
        if is_system_folder(normalized_old):
            raise InvalidFolderNameError(
                normalized_old, f"Cannot rename system folder '{normalized_old}'"
            )

        # Resolve actual folder name (case-insensitive lookup)
        actual_old_name = self._resolve_folder_name(normalized_old)
        if actual_old_name is None:
            raise FolderNotFoundError(normalized_old)

        # Resolve new path with correct case for existing parent folders.
        # This handles cases like renaming "TestFolder/Sub" to "testfolder/NewSub"
        # where "TestFolder" already exists - we must use "TestFolder", not "testfolder".
        resolved_new = self._resolve_path_with_existing_parents(normalized_new)

        # Check if new name already exists
        if self.folder_exists(resolved_new):
            raise FolderAlreadyExistsError(resolved_new)

        # Ensure parent folders for new path exist
        self._ensure_parent_folders_exist(resolved_new)

        # Rename via IMAP RENAME command using the actual folder name
        old_imap_path = f"Folders/{actual_old_name}"
        new_imap_path = f"Folders/{resolved_new}"
        quoted_old = _quote_folder_name(old_imap_path)
        quoted_new = _quote_folder_name(new_imap_path)

        def _rename_folder() -> Any:
            """Execute IMAP RENAME command."""
            status, data = self._connection_manager.connection.rename(quoted_old, quoted_new)
            if status != "OK":
                raise FolderError(f"IMAP RENAME failed with status: {status}, data: {data}")
            return data

        try:
            self._connection_manager.execute_with_retry(_rename_folder)

            # Return the renamed folder
            message_count = self._get_folder_message_count(new_imap_path)
            return Folder(
                name=resolved_new,
                full_path=new_imap_path,
                is_system=False,
                message_count=message_count,
            )

        except BridgeConnectionError:
            raise
        except FolderError:
            raise
        except Exception as e:
            raise FolderError(
                f"Failed to rename folder '{normalized_old}' to '{resolved_new}': {e}"
            ) from e

    def delete_folder(self, name: str) -> None:
        """
        Delete a custom folder.

        Note: Folder lookup is case-insensitive. If you pass "MyFolder" but the
        actual folder is named "myfolder", it will still be found and deleted.

        Args:
            name: Folder name or path to delete (case-insensitive)

        Raises:
            FolderNotFoundError: If folder doesn't exist
            InvalidFolderNameError: If trying to delete system folder
            FolderError: If deletion fails
        """
        # Normalize and validate name
        normalized_name = normalize_folder_path(name)
        if not normalized_name:
            raise InvalidFolderNameError(name, "Folder name cannot be empty")

        # Cannot delete system folders
        if is_system_folder(normalized_name):
            raise InvalidFolderNameError(
                normalized_name, f"Cannot delete system folder '{normalized_name}'"
            )

        # Resolve actual folder name (case-insensitive lookup)
        actual_name = self._resolve_folder_name(normalized_name)
        if actual_name is None:
            raise FolderNotFoundError(normalized_name)

        # Delete via IMAP DELETE command using the actual folder name
        imap_path = f"Folders/{actual_name}"
        quoted_path = _quote_folder_name(imap_path)

        def _delete_folder() -> Any:
            """Execute IMAP DELETE command."""
            status, data = self._connection_manager.connection.delete(quoted_path)
            if status != "OK":
                raise FolderError(f"IMAP DELETE failed with status: {status}, data: {data}")
            return data

        try:
            self._connection_manager.execute_with_retry(_delete_folder)

        except BridgeConnectionError:
            raise
        except FolderError:
            raise
        except Exception as e:
            raise FolderError(f"Failed to delete folder '{normalized_name}': {e}") from e

    def _ensure_parent_folders_exist(self, folder_path: str) -> None:
        """
        Ensure all parent folders in a path exist, creating them if necessary.

        For path "foo/bar/baz", ensures "foo" and "foo/bar" exist before creating "baz".

        Args:
            folder_path: The target folder path

        Raises:
            FolderError: If parent folder creation fails
        """
        parts = split_folder_path(folder_path)
        if len(parts) <= 1:
            # No parent folders needed
            return

        # Create parent folders from top down (excluding the final part)
        for i in range(1, len(parts)):
            parent_path = "/".join(parts[:i])
            if not self.folder_exists(parent_path):
                self._create_single_folder(parent_path)

    def _create_single_folder(self, folder_name: str) -> None:
        """
        Create a single folder without checking for parents.

        Internal helper method used by _ensure_parent_folders_exist.

        Args:
            folder_name: The folder name (without Folders/ prefix)

        Raises:
            FolderError: If folder creation fails
        """
        imap_path = f"Folders/{folder_name}"
        quoted_path = _quote_folder_name(imap_path)

        def _create() -> Any:
            """Execute IMAP CREATE command."""
            status, data = self._connection_manager.connection.create(quoted_path)
            if status != "OK":
                raise FolderError(
                    f"Failed to create folder '{folder_name}': status={status}, data={data}"
                )
            return data

        try:
            self._connection_manager.execute_with_retry(_create)
        except Exception as e:
            raise FolderError(f"Failed to create folder '{folder_name}': {e}") from e
