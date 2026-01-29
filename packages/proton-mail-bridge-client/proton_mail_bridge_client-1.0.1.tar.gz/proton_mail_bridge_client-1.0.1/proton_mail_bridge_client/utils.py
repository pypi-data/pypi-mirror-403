"""
Utility functions for proton-mail-bridge-client.

Helper functions for IMAP response parsing, email header decoding,
date/time conversion, and encoding handling.
"""

import email.header
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

# Pre-compiled regex patterns for performance
_EMAIL_BRACKET_RE = re.compile(r"<([^>]+)>")
_MULTI_SLASH_RE = re.compile(r"/+")


def _decode_bytes_safe(data: bytes, fallback: str = "replace") -> str:
    """Decode bytes trying UTF-8 first, then latin-1 with error handling."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors=fallback)


def parse_imap_list_response(response_line: bytes) -> tuple[str, str, str] | None:
    """
    Parse a single IMAP LIST response line.

    Properly handles escaped characters in folder names (backslashes and quotes).
    IMAP protocol escapes these characters in the wire format, but we need to
    unescape them to get the actual folder name.

    Args:
        response_line: Raw IMAP LIST response (e.g., b'(\\HasNoChildren) "/" "INBOX"')

    Returns:
        Tuple of (flags, delimiter, folder_name) or None if parsing fails

    Example:
        >>> parse_imap_list_response(b'(\\HasNoChildren) "/" "INBOX"')
        ('\\HasNoChildren', '/', 'INBOX')
        >>> parse_imap_list_response(b'(\\HasNoChildren) "/" "Test\\\\"Folder"')
        ('\\HasNoChildren', '/', 'Test"Folder')
    """
    try:
        response_str = response_line.decode("utf-8")

        # Pattern: (flags) "delimiter" "folder_name"
        # The folder_name can contain escaped quotes and backslashes
        # Use a regex that handles escaped characters: (?:[^"\\]|\\.)*
        # This matches either non-quote-non-backslash OR backslash-followed-by-anything
        match = re.match(r'\(([^)]*)\)\s+"([^"]*)"\s+"((?:[^"\\]|\\.)*)"', response_str)
        if match:
            flags = match.group(1)
            delimiter = match.group(2)
            folder_name = match.group(3)
            # Unescape the folder name: \" → ", \\ → \
            folder_name = folder_name.replace('\\"', '"').replace("\\\\", "\\")
            return (flags, delimiter, folder_name)

        # Alternative pattern without quotes around folder name
        match = re.match(r'\(([^)]*)\)\s+"([^"]*)"\s+(\S+)', response_str)
        if match:
            flags = match.group(1)
            delimiter = match.group(2)
            folder_name = match.group(3)
            # Folder name might still be escaped even without quotes
            folder_name = folder_name.replace('\\"', '"').replace("\\\\", "\\")
            return (flags, delimiter, folder_name)

    except Exception:  # nosec B110 - resilience: return None for unparseable server responses
        pass

    return None


def decode_header(header_value: str) -> str:
    """
    Decode email header that may be RFC 2047 encoded.

    Handles headers like "=?UTF-8?B?VGVzdA==?=" and returns plain text.

    Args:
        header_value: Raw header value

    Returns:
        Decoded header string

    Example:
        >>> decode_header("=?UTF-8?B?SGVsbG8gV29ybGQ=?=")
        'Hello World'
    """
    if not header_value:
        return ""

    try:
        decoded_parts = email.header.decode_header(header_value)
        result_parts = []

        for content, charset in decoded_parts:
            if isinstance(content, bytes):
                if charset:
                    try:
                        result_parts.append(content.decode(charset))
                    except (UnicodeDecodeError, LookupError):
                        # Specified charset failed, use fallback decoding
                        result_parts.append(_decode_bytes_safe(content))
                else:
                    # No charset specified, use fallback decoding
                    result_parts.append(_decode_bytes_safe(content))
            else:
                result_parts.append(content)

        return "".join(result_parts)
    except Exception:
        # If decoding fails, return original
        return header_value


def parse_email_date(date_str: str) -> datetime | None:
    """
    Parse email date string to datetime object.

    Handles various email date formats per RFC 2822/5322.

    Args:
        date_str: Email date string

    Returns:
        datetime object or None if parsing fails

    Example:
        >>> parse_email_date("Mon, 06 Jan 2026 10:00:00 +0000")
        datetime.datetime(2026, 1, 6, 10, 0, tzinfo=...)
    """
    if not date_str:
        return None

    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def parse_address_list(address_str: str) -> list[str]:
    """
    Parse comma-separated email addresses.

    Args:
        address_str: Comma-separated addresses (e.g., "user1@example.com, user2@example.com")

    Returns:
        List of email addresses

    Example:
        >>> parse_address_list("Alice <alice@example.com>, bob@example.com")
        ['alice@example.com', 'bob@example.com']
    """
    if not address_str:
        return []

    # Split by comma
    addresses = []
    for addr in address_str.split(","):
        addr = addr.strip()

        # Extract email from "Name <email>" format
        match = _EMAIL_BRACKET_RE.search(addr)
        if match:
            addresses.append(match.group(1))
        elif "@" in addr:
            # Plain email address
            addresses.append(addr)

    return addresses


def extract_email_from_address(address: str) -> str:
    """
    Extract just the email address from "Name <email>" format.

    Args:
        address: Email address with optional name

    Returns:
        Just the email address

    Example:
        >>> extract_email_from_address("Alice <alice@example.com>")
        'alice@example.com'
        >>> extract_email_from_address("bob@example.com")
        'bob@example.com'
    """
    if not address:
        return ""

    # Check for "Name <email>" format
    match = _EMAIL_BRACKET_RE.search(address)
    if match:
        return match.group(1)

    # Return as-is if no angle brackets
    return address.strip()


def is_system_folder(folder_name: str) -> bool:
    """
    Determine if a folder is a system folder.

    System folders are: INBOX, Sent, Drafts, Archive, Spam, Trash, All Mail
    Also includes "Folders" and "Labels" containers which are internal structure.

    Args:
        folder_name: Folder name to check

    Returns:
        True if system folder, False otherwise
    """
    system_folders = {
        "INBOX",
        "Sent",
        "Drafts",
        "Archive",
        "Spam",
        "Trash",
        "All Mail",
        "Sent Messages",
        "Deleted Messages",
        "Junk",
        "Folders",  # Container for custom folders
        "Labels",  # Container for labels
        "Starred",  # Added from ProtonMail documentation
    }

    return folder_name in system_folders


def is_custom_folder(folder_name: str) -> bool:
    """
    Check if a folder is a custom folder (subfolder of "Folders").

    Args:
        folder_name: Folder name to check

    Returns:
        True if custom folder, False otherwise

    Example:
        >>> is_custom_folder("Folders/MyFolder")
        True
        >>> is_custom_folder("INBOX")
        False
    """
    return folder_name.startswith("Folders/")


def is_label_folder(folder_name: str) -> bool:
    """
    Check if a folder is a label (subfolder of "Labels").

    Args:
        folder_name: Folder name to check

    Returns:
        True if label folder, False otherwise

    Example:
        >>> is_label_folder("Labels/MyLabel")
        True
        >>> is_label_folder("INBOX")
        False
    """
    return folder_name.startswith("Labels/")


def strip_folder_prefix(folder_name: str) -> str:
    """
    Remove "Folders/" prefix from a folder name.

    Args:
        folder_name: Folder name with potential prefix

    Returns:
        Folder name without "Folders/" prefix

    Example:
        >>> strip_folder_prefix("Folders/MyFolder")
        'MyFolder'
        >>> strip_folder_prefix("INBOX")
        'INBOX'
    """
    return folder_name.removeprefix("Folders/")


def strip_label_prefix(folder_name: str) -> str:
    """
    Remove "Labels/" prefix from a label name.

    Args:
        folder_name: Label name with potential prefix

    Returns:
        Label name without "Labels/" prefix

    Example:
        >>> strip_label_prefix("Labels/MyLabel")
        'MyLabel'
        >>> strip_label_prefix("Important")
        'Important'
    """
    return folder_name.removeprefix("Labels/")


def safe_decode_bytes(data: bytes, fallback: str = "replace") -> str:
    """
    Safely decode bytes to string, trying multiple encodings.

    Tries UTF-8 first, then latin-1 with error handling.

    Args:
        data: Bytes to decode
        fallback: Error handling strategy ('replace', 'ignore', 'strict')

    Returns:
        Decoded string
    """
    if not data:
        return ""
    return _decode_bytes_safe(data, fallback)


def parse_imap_address(address_structure: str) -> str:
    """
    Parse IMAP address structure to email address string.

    IMAP address format: (("name" NIL "mailbox" "host"))
    or multiple addresses: (("name1" NIL "mailbox1" "host1") ("name2" NIL "mailbox2" "host2"))
    or NIL for empty

    Args:
        address_structure: IMAP address structure string

    Returns:
        Formatted email address (e.g., "Name <email@host>" or "email@host")
        Returns empty string if parsing fails or structure is NIL

    Example:
        >>> parse_imap_address('(("John Doe" NIL "john" "example.com"))')
        'John Doe <john@example.com>'
        >>> parse_imap_address('((NIL NIL "john" "example.com"))')
        'john@example.com'
    """
    if not address_structure or address_structure.strip() == "NIL":
        return ""

    try:
        # Extract first address from structure
        # Format: (("name" NIL "mailbox" "host"))
        # We want to extract: name, mailbox, host

        # Remove outer parentheses
        addr_str = address_structure.strip()
        if addr_str.startswith("(("):
            addr_str = addr_str[2:]
        if addr_str.endswith("))"):
            addr_str = addr_str[:-2]

        # Parse quoted strings and atoms
        # Pattern: "name" NIL "mailbox" "host" or NIL NIL "mailbox" "host"
        parts = []
        current = ""
        in_quotes = False
        i = 0

        while i < len(addr_str):
            char = addr_str[i]

            if char == '"' and (i == 0 or addr_str[i - 1] != "\\"):
                if in_quotes:
                    # End of quoted string
                    parts.append(current)
                    current = ""
                    in_quotes = False
                else:
                    # Start of quoted string
                    in_quotes = True
                i += 1
                continue

            if in_quotes:
                # Inside quotes, collect everything
                current += char
                i += 1
                continue

            # Outside quotes
            if char == " ":
                if current:
                    parts.append(current)
                    current = ""
                i += 1
                continue

            current += char
            i += 1

        # Add last part
        if current:
            parts.append(current)

        # Now we should have 4 parts: [name, NIL, mailbox, host]
        if len(parts) >= 4:
            name = parts[0] if parts[0] != "NIL" else ""
            mailbox = parts[2] if parts[2] != "NIL" else ""
            host = parts[3] if parts[3] != "NIL" else ""

            if mailbox and host:
                email_addr = f"{mailbox}@{host}"
                if name:
                    return f"{name} <{email_addr}>"
                return email_addr

        return ""

    except Exception:
        return ""


def parse_imap_envelope(envelope_str: str) -> dict[str, str | None]:
    """
    Parse IMAP ENVELOPE structure into a dictionary.

    ENVELOPE format (RFC 3501):
    (date subject from sender reply-to to cc bcc in-reply-to message-id)

    Args:
        envelope_str: ENVELOPE structure string from IMAP FETCH

    Returns:
        Dictionary with keys: date, subject, from, sender, reply_to, to, cc, bcc,
        in_reply_to, message_id. Values are strings or None.

    Example:
        >>> envelope = '("Mon, 06 Jan 2026 10:00:00 +0000" "Test Subject" ...)'
        >>> result = parse_imap_envelope(envelope)
        >>> result['subject']
        'Test Subject'
    """
    result: dict[str, str | None] = {
        "date": None,
        "subject": None,
        "from": None,
        "sender": None,
        "reply_to": None,
        "to": None,
        "cc": None,
        "bcc": None,
        "in_reply_to": None,
        "message_id": None,
    }

    if not envelope_str:
        return result

    try:
        # Remove outer parentheses from ENVELOPE structure
        env = envelope_str.strip()
        if env.startswith("("):
            env = env[1:]
        if env.endswith(")"):
            env = env[:-1]

        # Parse ENVELOPE fields
        # We need to handle quoted strings and nested parentheses
        fields = []
        current = ""
        depth = 0
        in_quotes = False
        i = 0

        while i < len(env):
            char = env[i]

            # Handle escape sequences in quotes
            if char == "\\" and in_quotes and i + 1 < len(env):
                current += char + env[i + 1]
                i += 2
                continue

            # Handle quotes
            if char == '"':
                in_quotes = not in_quotes
                current += char
                i += 1
                continue

            # Handle parentheses (for nested structures like addresses)
            if not in_quotes:
                if char == "(":
                    depth += 1
                    current += char
                    i += 1
                    continue
                elif char == ")":
                    depth -= 1
                    current += char
                    i += 1
                    continue

                # Space separates fields (only at depth 0)
                if char == " " and depth == 0:
                    if current.strip():
                        fields.append(current.strip())
                        current = ""
                    i += 1
                    continue

            current += char
            i += 1

        # Add last field
        if current.strip():
            fields.append(current.strip())

        # Extract fields (ENVELOPE has exactly 10 fields)
        field_names = [
            "date",
            "subject",
            "from",
            "sender",
            "reply_to",
            "to",
            "cc",
            "bcc",
            "in_reply_to",
            "message_id",
        ]

        for idx, field_name in enumerate(field_names):
            if idx < len(fields):
                field_value = fields[idx]

                # Remove quotes from simple strings
                if field_value.startswith('"') and field_value.endswith('"'):
                    field_value = field_value[1:-1]

                # Convert NIL to None
                if field_value == "NIL":
                    result[field_name] = None
                # Parse addresses (fields with parentheses)
                elif field_name in ("from", "sender", "reply_to", "to", "cc", "bcc"):
                    result[field_name] = parse_imap_address(field_value)
                else:
                    result[field_name] = field_value

        return result

    except Exception:
        return result


def normalize_folder_path(name: str) -> str:
    """
    Normalize a folder path by cleaning up common issues.

    - Strips leading/trailing whitespace and slashes
    - Collapses double slashes to single slashes
    - Returns empty string if name is only whitespace/slashes

    Args:
        name: Folder name or path to normalize

    Returns:
        Normalized folder path

    Example:
        >>> normalize_folder_path("  foo/bar  ")
        'foo/bar'
        >>> normalize_folder_path("foo//bar")
        'foo/bar'
        >>> normalize_folder_path("/foo/bar/")
        'foo/bar'
        >>> normalize_folder_path("///")
        ''
    """
    if not name:
        return ""

    # Strip whitespace
    result = name.strip()

    # Strip leading/trailing slashes
    result = result.strip("/")

    # Collapse multiple slashes to single (single-pass via regex)
    result = _MULTI_SLASH_RE.sub("/", result)

    return result


def split_folder_path(name: str) -> list[str]:
    """
    Split a folder path into its component parts.

    Normalizes the path first, then splits on '/'.

    Args:
        name: Folder name or path to split

    Returns:
        List of path components (empty list if name is empty/invalid)

    Example:
        >>> split_folder_path("foo/bar/baz")
        ['foo', 'bar', 'baz']
        >>> split_folder_path("single")
        ['single']
        >>> split_folder_path("")
        []
        >>> split_folder_path("foo//bar")
        ['foo', 'bar']
    """
    normalized = normalize_folder_path(name)
    if not normalized:
        return []
    return normalized.split("/")


def validate_folder_name(name: str) -> None:
    """
    Validate a folder name for problematic characters.

    Rejects control characters, non-ASCII characters, and other problematic
    characters that can cause issues with IMAP operations or folder management.

    Args:
        name: Folder name to validate (after normalization)

    Raises:
        ValueError: If name contains invalid characters

    Example:
        >>> validate_folder_name("MyFolder")  # OK
        >>> validate_folder_name("My\\nFolder")  # Raises ValueError
        >>> validate_folder_name("My🔥Folder")  # Raises ValueError (non-ASCII)
    """
    # Define problematic characters
    # Control characters: \n \r \t \0 and other ASCII control chars (0x00-0x1F, 0x7F)
    # Also reject some IMAP-problematic characters
    invalid_chars = {
        "\n": "\\n (newline)",
        "\r": "\\r (carriage return)",
        "\t": "\\t (tab)",
        "\0": "\\0 (null)",
        "\x0b": "\\x0b (vertical tab)",
        "\x0c": "\\x0c (form feed)",
    }

    # Check for explicitly invalid characters
    for char, desc in invalid_chars.items():
        if char in name:
            raise ValueError(
                f"Folder name contains invalid character {desc}. "
                f"Folder names must not contain control characters."
            )

    # Check for other ASCII control characters (0x00-0x1F except what we already checked, and 0x7F)
    for char in name:
        code = ord(char)
        if code < 0x20 or code == 0x7F:
            raise ValueError(
                f"Folder name contains invalid control character (code {code}). "
                f"Folder names must not contain control characters."
            )

    # Check for non-ASCII characters (BUG #7 fix)
    # IMAP requires Modified UTF-7 encoding for non-ASCII, which we don't currently support
    try:
        name.encode("ascii")
    except UnicodeEncodeError as e:
        raise ValueError(
            "Folder name contains non-ASCII characters. "
            "Folder names must contain only ASCII characters (A-Z, a-z, 0-9, and common symbols). "
            "Emojis and Unicode characters are not supported."
        ) from e


def validate_label_name(name: str) -> None:
    """
    Validate a label name for problematic characters.

    Rejects control characters, non-ASCII characters, and other problematic
    characters that can cause issues with IMAP operations or label management.

    Args:
        name: Label name to validate (after stripping whitespace)

    Raises:
        ValueError: If name contains invalid characters

    Example:
        >>> validate_label_name("MyLabel")  # OK
        >>> validate_label_name("My\\nLabel")  # Raises ValueError
        >>> validate_label_name("My🔥Label")  # Raises ValueError (non-ASCII)
    """
    # Labels have same character restrictions as folders
    # (they're both IMAP folders under the hood)
    validate_folder_name(name)


def is_readonly_folder(folder_name: str) -> bool:
    """
    Determine if a folder is read-only (cannot move/delete emails from it).

    ProtonMail's "All Mail" folder is a special view that shows all messages.
    Operations like MOVE or DELETE are not allowed on it.

    Args:
        folder_name: Folder name to check

    Returns:
        True if folder is read-only, False otherwise

    Example:
        >>> is_readonly_folder("All Mail")
        True
        >>> is_readonly_folder("INBOX")
        False
    """
    readonly_folders = {
        "All Mail",
    }
    return folder_name in readonly_folders


def translate_imap_error(error_msg: str) -> str:
    """
    Translate technical IMAP error messages to user-friendly messages.

    Args:
        error_msg: Raw IMAP error message

    Returns:
        User-friendly error message

    Example:
        >>> translate_imap_error("UID command error: BAD [b'[Error offset=18]: expected valid digit']")
        'Invalid email ID format. Please provide a valid numeric email ID.'
    """
    error_lower = error_msg.lower()

    # Pattern: Invalid UID format
    # "expected valid digit" is specific enough to indicate a format error
    # Also check for "command error" context which indicates IMAP protocol errors
    if "expected valid digit" in error_lower or (
        "invalid syntax" in error_lower
        and ("uid" in error_lower or "email" in error_lower or "command error" in error_lower)
    ):
        return "Invalid email ID format. Please provide a valid numeric email ID."

    # Pattern: Email not found
    if "no matching messages" in error_lower or "no messages found" in error_lower:
        return "Email not found in the specified folder."

    # Pattern: Folder not found
    if "mailbox does not exist" in error_lower or "no such mailbox" in error_lower:
        return "Folder does not exist."

    # Pattern: Permission denied
    if "permission denied" in error_lower or "access denied" in error_lower:
        return "Operation not permitted on this folder."

    # Pattern: Connection issues
    if "connection" in error_lower and ("lost" in error_lower or "closed" in error_lower):
        return "Connection to ProtonMail Bridge was lost. Please check that Bridge is running."

    # Pattern: Timeout
    if "timeout" in error_lower or "timed out" in error_lower:
        return "Operation timed out. Please try again."

    # If no pattern matches, return original error
    # (at least we tried to make it better)
    return error_msg


def encode_imap_utf7(text: str) -> str:
    """
    Encode text to IMAP Modified UTF-7 (as specified in RFC 3501).

    IMAP uses a modified version of UTF-7 for mailbox names:
    - ASCII printable characters (0x20-0x7E except &) are represented as-is
    - '&' is represented as '&-'
    - Other characters are encoded in modified BASE64 between '&' and '-'
    - Modified BASE64 uses ',' instead of '/' and omits padding '='

    Args:
        text: Text to encode

    Returns:
        IMAP Modified UTF-7 encoded string

    Example:
        >>> encode_imap_utf7("Hello")
        'Hello'
        >>> encode_imap_utf7("Héllo")
        'H&AOk-llo'
        >>> encode_imap_utf7("你好")
        '&T2BZfQ-'
    """
    import base64

    if not text:
        return ""

    result = []
    i = 0

    while i < len(text):
        char = text[i]

        # ASCII printable characters (except &) pass through
        if 0x20 <= ord(char) <= 0x7E and char != "&":
            result.append(char)
            i += 1
        # & becomes &-
        elif char == "&":
            result.append("&-")
            i += 1
        # Non-ASCII characters need encoding
        else:
            # Collect consecutive non-ASCII characters (but NOT &, which has its own handling)
            j = i
            while j < len(text):
                c = text[j]
                if not (0x20 <= ord(c) <= 0x7E):
                    j += 1
                else:
                    break

            # Encode this chunk as modified UTF-7
            chunk = text[i:j]

            # Encode to UTF-16BE (big-endian, no BOM)
            utf16_bytes = chunk.encode("utf-16-be")

            # Base64 encode
            b64 = base64.b64encode(utf16_bytes).decode("ascii")

            # Modified BASE64: replace '/' with ',' and remove '='
            modified_b64 = b64.replace("/", ",").rstrip("=")

            # Wrap in &...-
            result.append(f"&{modified_b64}-")

            i = j

    return "".join(result)


def decode_imap_utf7(text: str | bytes) -> str:
    """
    Decode IMAP Modified UTF-7 text to Unicode string.

    Args:
        text: IMAP Modified UTF-7 encoded string or bytes

    Returns:
        Decoded Unicode string

    Example:
        >>> decode_imap_utf7("Hello")
        'Hello'
        >>> decode_imap_utf7("H&AOk-llo")
        'Héllo'
        >>> decode_imap_utf7("&T2BZfQ-")
        '你好'
    """
    import base64

    # Handle bytes input
    if isinstance(text, bytes):
        text = text.decode("ascii", errors="replace")

    if not text:
        return ""

    result = []
    i = 0

    while i < len(text):
        # Look for & marker
        if text[i] == "&":
            # Find the closing -
            j = i + 1
            while j < len(text) and text[j] != "-":
                j += 1

            if j < len(text):
                # Found closing -
                encoded = text[i + 1 : j]

                if not encoded:
                    # &- means literal &
                    result.append("&")
                else:
                    # Decode modified BASE64
                    # Replace ',' with '/' for standard BASE64
                    standard_b64 = encoded.replace(",", "/")

                    # Add padding if needed
                    padding = (4 - len(standard_b64) % 4) % 4
                    standard_b64 += "=" * padding

                    try:
                        # Decode BASE64 to get UTF-16BE bytes
                        utf16_bytes = base64.b64decode(standard_b64)

                        # Decode UTF-16BE to string
                        decoded = utf16_bytes.decode("utf-16-be")
                        result.append(decoded)
                    except Exception:
                        # Decoding failed, keep original
                        result.append(text[i : j + 1])

                i = j + 1
            else:
                # No closing -, treat as literal
                result.append(text[i])
                i += 1
        else:
            # Regular character
            result.append(text[i])
            i += 1

    return "".join(result)


def validate_email_uid(email_id: str, param_name: str = "email_id") -> None:
    """
    Validate that an email UID is a valid positive integer string.

    IMAP UIDs must be positive integers. This validation prevents
    type errors and provides clear error messages before they reach
    the IMAP layer.

    Args:
        email_id: The email UID to validate (as string)
        param_name: Parameter name for error messages (default: "email_id")

    Raises:
        ValueError: If email_id is not a valid positive integer string

    Example:
        >>> validate_email_uid("12345")  # OK
        >>> validate_email_uid("0")  # Raises ValueError (must be positive)
        >>> validate_email_uid("abc")  # Raises ValueError (not an integer)
        >>> validate_email_uid("")  # Raises ValueError (empty)
    """
    if not email_id or not email_id.strip():
        raise ValueError(f"{param_name} cannot be empty")

    # Check if it's a valid integer
    try:
        uid_int = int(email_id)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{param_name} must be a positive integer, got: {email_id!r}") from e

    # Check if it's positive
    if uid_int <= 0:
        raise ValueError(
            f"{param_name} must be a positive integer, got: {email_id} (IMAP UIDs start at 1)"
        )
