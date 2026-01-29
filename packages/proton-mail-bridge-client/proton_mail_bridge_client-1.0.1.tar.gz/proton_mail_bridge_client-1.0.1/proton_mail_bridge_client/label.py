"""
Label management for proton-mail-bridge-client.

Handles label operations. In ProtonMail Bridge, labels are exposed as subfolders
of the "Labels" IMAP folder. This module provides a label-specific API while using
the folder implementation, hiding the internal "Labels/" prefix from users.
"""

from typing import Any

from .connection import IMAPConnectionManager
from .exceptions import (
    BridgeConnectionError,
    InvalidLabelNameError,
    LabelAlreadyExistsError,
    LabelError,
    LabelNotFoundError,
)
from .folder import FolderManager, _quote_folder_name
from .utils import is_label_folder, strip_label_prefix, validate_label_name


class LabelManager:
    """
    Manages label operations.

    ProtonMail labels are exposed as subfolders under "Labels/" in Bridge's IMAP.
    This manager provides a label-centric API that hides the internal "Labels/"
    prefix from users, providing clean label names.

    Attributes:
        connection_manager: IMAP connection manager instance
        folder_manager: FolderManager for underlying folder operations
    """

    def __init__(
        self,
        connection_manager: IMAPConnectionManager,
        folder_manager: FolderManager,
    ):
        """
        Initialize LabelManager.

        Args:
            connection_manager: IMAP connection manager for Bridge access
            folder_manager: FolderManager for folder operations
        """
        self._connection_manager = connection_manager
        self._folder_manager = folder_manager

    def list_labels(self) -> list[str]:
        """
        List all user-created labels.

        Returns only labels (subfolders of "Labels/") with the "Labels/" prefix
        stripped for a clean API. System folders and custom folders are excluded.

        Returns:
            List of label names (as strings, without "Labels/" prefix)

        Raises:
            BridgeConnectionError: If connection to Bridge fails
            LabelError: If label list cannot be retrieved
        """
        try:
            # Fetch raw folders including labels
            raw_folders = self._folder_manager._fetch_folders_from_bridge(include_labels=True)

            # Filter for label folders only and strip prefix
            labels = []
            for folder in raw_folders:
                # Check the full_path (original IMAP name) for label structure
                if is_label_folder(folder.full_path):
                    label_name = strip_label_prefix(folder.full_path)
                    labels.append(label_name)

            return labels

        except BridgeConnectionError:
            raise
        except Exception as e:
            raise LabelError(f"Failed to list labels: {e}") from e

    def label_exists(self, label_name: str) -> bool:
        """
        Check if a label exists.

        Note: Comparison is case-insensitive because ProtonMail Bridge
        does not allow labels with the same name but different case.

        Args:
            label_name: Name of the label to check

        Returns:
            True if label exists (and is not a system folder), False otherwise

        Raises:
            BridgeConnectionError: If connection to Bridge fails
        """
        return self._resolve_label_name(label_name) is not None

    def _resolve_label_name(self, label_name: str) -> str | None:
        """
        Resolve a label name to its actual name with correct casing.

        ProtonMail Bridge handles label names case-insensitively, so we need
        to find the actual label name as stored to use in IMAP operations.

        Args:
            label_name: The label name to resolve (case-insensitive)

        Returns:
            The actual label name with correct casing, or None if not found

        Raises:
            BridgeConnectionError: If connection to Bridge fails
        """
        try:
            labels = self.list_labels()
            label_name_lower = label_name.lower()
            for label in labels:
                if label.lower() == label_name_lower:
                    return label
            return None
        except BridgeConnectionError:
            raise
        except Exception:
            return None

    def _validate_label_name(self, name: str, field_desc: str = "Label name") -> str:
        """
        Validate and normalize a label name.

        Strips whitespace and checks for invalid characters/empty names.
        Labels are flat (no hierarchy), so "/" is not allowed.
        Control characters are also rejected.

        Args:
            name: The label name to validate
            field_desc: Description for error messages (e.g., "Old label name")

        Returns:
            The stripped, validated label name

        Raises:
            InvalidLabelNameError: If name is empty, contains "/", or has control characters
        """
        name = name.strip()
        if not name:
            raise InvalidLabelNameError(name, f"{field_desc} cannot be empty")
        if "/" in name:
            raise InvalidLabelNameError(
                name, "Label names cannot contain '/'. Labels are flat (no hierarchy)."
            )

        # Validate for control characters (Issue #3 fix)
        try:
            validate_label_name(name)
        except ValueError as e:
            raise InvalidLabelNameError(name, str(e)) from e

        return name

    def create_label(self, name: str) -> str:
        """
        Create a new label, or return existing label if it already exists.

        This operation is idempotent: calling it multiple times with the same name
        is safe and will return the existing label name. The returned name
        reflects the actual case as stored on the server.

        Args:
            name: Label name (cannot contain "/")

        Returns:
            The created or existing label name. If the label already existed,
            the returned name reflects the actual case (e.g., requesting "Important"
            when "important" exists returns "important").

        Raises:
            InvalidLabelNameError: If name contains "/" or is empty
            LabelError: If creation fails
        """
        name = self._validate_label_name(name)

        # Check if label already exists (case-insensitive)
        actual_name = self._resolve_label_name(name)
        if actual_name is not None:
            # Return the existing label with its actual case
            return actual_name

        # Create the label via IMAP CREATE command
        imap_path = f"Labels/{name}"
        quoted_path = _quote_folder_name(imap_path)

        def _create_label() -> Any:
            """Execute IMAP CREATE command."""
            status, data = self._connection_manager.connection.create(quoted_path)
            if status != "OK":
                raise LabelError(f"IMAP CREATE failed with status: {status}, data: {data}")
            return data

        try:
            self._connection_manager.execute_with_retry(_create_label)
            return name

        except BridgeConnectionError:
            raise
        except LabelError:
            raise
        except Exception as e:
            raise LabelError(f"Failed to create label '{name}': {e}") from e

    def rename_label(self, old_name: str, new_name: str) -> str:
        """
        Rename an existing label.

        Note: Label lookup is case-insensitive. If you pass "MyLabel" but the
        actual label is named "mylabel", it will still be found and renamed.

        Args:
            old_name: Current label name (case-insensitive)
            new_name: New label name (cannot contain "/")

        Returns:
            The new label name

        Raises:
            LabelNotFoundError: If old label doesn't exist
            LabelAlreadyExistsError: If new name already exists
            InvalidLabelNameError: If names contain "/" or are empty
            LabelError: If rename fails
        """
        old_name = self._validate_label_name(old_name, "Old label name")
        new_name = self._validate_label_name(new_name, "New label name")

        # Fetch labels once for both checks (avoids double IMAP call)
        labels = self.list_labels()
        labels_lower = {label.lower(): label for label in labels}

        # Resolve actual old name (case-insensitive)
        actual_old_name = labels_lower.get(old_name.lower())
        if actual_old_name is None:
            raise LabelNotFoundError(old_name)

        # Check new name doesn't already exist
        if new_name.lower() in labels_lower:
            raise LabelAlreadyExistsError(new_name)

        # Rename via IMAP RENAME command using the actual label name
        old_imap_path = f"Labels/{actual_old_name}"
        new_imap_path = f"Labels/{new_name}"
        quoted_old = _quote_folder_name(old_imap_path)
        quoted_new = _quote_folder_name(new_imap_path)

        def _rename_label() -> Any:
            """Execute IMAP RENAME command."""
            status, data = self._connection_manager.connection.rename(quoted_old, quoted_new)
            if status != "OK":
                raise LabelError(f"IMAP RENAME failed with status: {status}, data: {data}")
            return data

        try:
            self._connection_manager.execute_with_retry(_rename_label)
            return new_name

        except BridgeConnectionError:
            raise
        except LabelError:
            raise
        except Exception as e:
            raise LabelError(f"Failed to rename label '{old_name}' to '{new_name}': {e}") from e

    def delete_label(self, name: str) -> None:
        """
        Delete a label.

        Note: Label lookup is case-insensitive. If you pass "MyLabel" but the
        actual label is named "mylabel", it will still be found and deleted.

        Args:
            name: Label name to delete (case-insensitive)

        Raises:
            LabelNotFoundError: If label doesn't exist
            InvalidLabelNameError: If name is empty or contains "/"
            LabelError: If deletion fails
        """
        name = self._validate_label_name(name)

        # Resolve actual label name (case-insensitive lookup)
        actual_name = self._resolve_label_name(name)
        if actual_name is None:
            raise LabelNotFoundError(name)

        # Delete via IMAP DELETE command using the actual label name
        imap_path = f"Labels/{actual_name}"
        quoted_path = _quote_folder_name(imap_path)

        def _delete_label() -> Any:
            """Execute IMAP DELETE command."""
            status, data = self._connection_manager.connection.delete(quoted_path)
            if status != "OK":
                raise LabelError(f"IMAP DELETE failed with status: {status}, data: {data}")
            return data

        try:
            self._connection_manager.execute_with_retry(_delete_label)

        except BridgeConnectionError:
            raise
        except LabelError:
            raise
        except Exception as e:
            raise LabelError(f"Failed to delete label '{name}': {e}") from e
