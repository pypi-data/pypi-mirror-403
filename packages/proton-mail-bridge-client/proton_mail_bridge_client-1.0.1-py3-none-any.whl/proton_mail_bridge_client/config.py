"""
Configuration management for proton-mail-bridge-client.

Handles default constants and environment variable loading for ProtonMail Bridge connection.
"""

import os
import re
import shutil
import subprocess  # nosec B404 - required for SOPS CLI decryption
from dataclasses import dataclass
from pathlib import Path

# Default connection settings
DEFAULT_IMAP_HOST = "127.0.0.1"
DEFAULT_IMAP_PORT = 1143
DEFAULT_SMTP_HOST = "127.0.0.1"
DEFAULT_SMTP_PORT = 1025
DEFAULT_CONNECTION_TIMEOUT = 30
MAX_RECONNECTION_ATTEMPTS = 3

# Environment variable names
ENV_BRIDGE_EMAIL = "PROTONMAIL_BRIDGE_EMAIL"
ENV_BRIDGE_PASSWORD = "PROTONMAIL_BRIDGE_PASSWORD"  # nosec B105 - env var name, not a password
ENV_BRIDGE_HOST = "PROTONMAIL_BRIDGE_HOST"
ENV_BRIDGE_PORT = "PROTONMAIL_BRIDGE_PORT"

# Pre-compiled regex for parsing dotenv KEY=value lines
# Matches: valid identifier (starts with letter/underscore) = any value
_DOTENV_LINE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


@dataclass
class ConnectionConfig:
    """
    Configuration for ProtonMail Bridge connection.

    Attributes:
        email: ProtonMail email address
        password: ProtonMail Bridge password (not account password)
        host: Bridge IMAP host
        port: Bridge IMAP port
        timeout: Connection timeout in seconds
    """

    email: str
    password: str
    host: str = DEFAULT_IMAP_HOST
    port: int = DEFAULT_IMAP_PORT
    timeout: int = DEFAULT_CONNECTION_TIMEOUT


def load_config_from_sops(file_path: str = ".env.sops") -> dict[str, str] | None:
    """
    Decrypt and parse SOPS-encrypted environment file using SOPS CLI.

    Args:
        file_path: Path to SOPS-encrypted file (default: .env.sops)

    Returns:
        Dict of environment variables from SOPS file, or None if file doesn't exist
        or SOPS is not installed.

    Raises:
        SOPSDecryptionError: If file exists but decryption fails.
    """
    # Import here to avoid circular import (exceptions imports from this module)
    from proton_mail_bridge_client.exceptions import SOPSDecryptionError

    # Check if file exists
    if not Path(file_path).exists():
        return None

    # Check if SOPS is available
    if not shutil.which("sops"):
        return None

    # Decrypt file using SOPS
    try:
        result = subprocess.run(  # nosec B603 B607 - sops is validated via shutil.which above
            ["sops", "-d", file_path],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise SOPSDecryptionError(
                file_path,
                f"SOPS decryption failed with exit code {result.returncode}: {result.stderr.strip()}",
            )

        # Parse dotenv format from decrypted content
        env_vars = {}
        for line in result.stdout.splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse key=value pairs using pre-compiled pattern
            match = _DOTENV_LINE_PATTERN.match(line)
            if match:
                key, value = match.groups()

                # Remove surrounding quotes if present
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                env_vars[key] = value

        return env_vars

    except (OSError, subprocess.SubprocessError) as e:
        raise SOPSDecryptionError(file_path, f"Error running SOPS: {e!s}") from e


def load_config_from_env() -> ConnectionConfig | None:
    """
    Load connection configuration from SOPS file and environment variables.

    Configuration precedence (highest to lowest):
    1. Shell environment variables
    2. SOPS-encrypted file (.env.sops)

    Returns:
        ConnectionConfig if all required env vars are set, None otherwise.

    Raises:
        ValueError: If PROTONMAIL_BRIDGE_PORT is set but not a valid integer.

    Environment Variables:
        PROTONMAIL_BRIDGE_EMAIL: ProtonMail email address
        PROTONMAIL_BRIDGE_PASSWORD: Bridge password
        PROTONMAIL_BRIDGE_HOST: Bridge host (optional, default: 127.0.0.1)
        PROTONMAIL_BRIDGE_PORT: Bridge port (optional, default: 1143)
    """
    # Load SOPS variables (silent if file missing or SOPS not installed)
    sops_vars = load_config_from_sops() or {}

    # Merge with shell environment (shell takes precedence)
    merged_env = {**sops_vars, **dict(os.environ)}

    # Extract configuration values
    email = merged_env.get(ENV_BRIDGE_EMAIL)
    password = merged_env.get(ENV_BRIDGE_PASSWORD)

    if not email or not password:
        return None

    host = merged_env.get(ENV_BRIDGE_HOST, DEFAULT_IMAP_HOST)

    # Parse and validate port
    port_str = merged_env.get(ENV_BRIDGE_PORT)
    if port_str is not None:
        try:
            port = int(port_str)
        except ValueError as e:
            raise ValueError(
                f"Invalid {ENV_BRIDGE_PORT}: '{port_str}' is not a valid port number"
            ) from e
    else:
        port = DEFAULT_IMAP_PORT

    return ConnectionConfig(email=email, password=password, host=host, port=port)
