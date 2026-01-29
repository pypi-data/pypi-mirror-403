"""
IMAP connection management for proton-mail-bridge-client.

Handles persistent IMAP connections with automatic reconnection and retry logic.
"""

import contextlib
import imaplib
import ssl
import threading
import time
from collections.abc import Callable
from typing import Any

from .config import MAX_RECONNECTION_ATTEMPTS
from .exceptions import (
    BridgeAuthenticationError,
    BridgeConnectionError,
    BridgeTimeoutError,
)

# Capture the abort exception class at module level to avoid issues with mocking.
# When tests mock imaplib.IMAP4, the abort class would become a Mock object
# which cannot be used in except clauses.
IMAP4Abort = imaplib.IMAP4.abort


class IMAPConnectionManager:
    """
    Manages persistent IMAP connection to ProtonMail Bridge.

    Provides automatic reconnection with exponential backoff, connection health
    monitoring, and thread-safe access to the IMAP connection.

    Attributes:
        host: Bridge IMAP host
        port: Bridge IMAP port
        email: ProtonMail email address
        password: Bridge password
        timeout: Connection timeout in seconds
    """

    def __init__(self, host: str, port: int, email: str, password: str, timeout: int = 30):
        """
        Initialize connection manager.

        Args:
            host: Bridge IMAP host (typically 127.0.0.1)
            port: Bridge IMAP port (typically 1143)
            email: ProtonMail email address
            password: Bridge password (NOT ProtonMail account password)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.email = email
        self._password = password  # Private to avoid accidental logging
        self.timeout = timeout

        self._connection: imaplib.IMAP4 | None = None
        self._lock = threading.RLock()
        self._connected = False

    def connect(self) -> None:
        """
        Establish connection to ProtonMail Bridge.

        Creates IMAP connection, upgrades to TLS with STARTTLS, and authenticates.

        Raises:
            BridgeConnectionError: If connection fails
            BridgeAuthenticationError: If authentication fails
            BridgeTimeoutError: If connection times out
        """
        with self._lock:
            try:
                # Connect to Bridge (no SSL initially, will use STARTTLS)
                self._connection = imaplib.IMAP4(self.host, self.port)
                self._connection.sock.settimeout(self.timeout)

                # Upgrade to TLS with STARTTLS
                # ProtonMail Bridge uses self-signed certificates, so we need to disable verification
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self._connection.starttls(ssl_context)

                # Authenticate
                try:
                    self._connection.login(self.email, self._password)
                except imaplib.IMAP4.error as e:
                    error_msg = str(e).lower()
                    if "auth" in error_msg or "login" in error_msg or "password" in error_msg:
                        raise BridgeAuthenticationError(
                            f"Authentication failed for {self.email}. "
                            "Verify you're using the Bridge password (not account password)"
                        ) from e
                    raise

                self._connected = True

            except TimeoutError as e:
                raise BridgeTimeoutError(
                    f"Connection to Bridge at {self.host}:{self.port} timed out"
                ) from e
            except OSError as e:
                raise BridgeConnectionError(
                    f"Cannot connect to Bridge at {self.host}:{self.port}. "
                    "Is ProtonMail Bridge running?"
                ) from e
            except imaplib.IMAP4.error as e:
                if not isinstance(e, BridgeAuthenticationError):
                    raise BridgeConnectionError(f"IMAP error: {e}") from e
                raise

    def disconnect(self) -> None:
        """
        Cleanly disconnect from Bridge.

        Logs out and closes the connection.
        """
        with self._lock:
            if self._connection and self._connected:
                try:
                    self._connection.logout()
                except Exception:  # nosec B110 - cleanup: errors during disconnect are irrelevant
                    # Ignore errors during disconnect
                    pass
                finally:
                    self._connection = None
                    self._connected = False

    def is_connected(self) -> bool:
        """
        Check if connection is established and healthy.

        Returns:
            True if connected, False otherwise
        """
        with self._lock:
            if not self._connected or not self._connection:
                return False

            # Try a simple NOOP command to verify connection health
            try:
                status, _ = self._connection.noop()
                return status == "OK"
            except Exception:
                self._connected = False
                return False

    def reconnect(self) -> None:
        """
        Reconnect to Bridge after connection loss.

        Disconnects existing connection and establishes a new one.

        Raises:
            BridgeConnectionError: If reconnection fails
            BridgeAuthenticationError: If authentication fails
        """
        self.disconnect()
        self.connect()

    def get_connection(self) -> imaplib.IMAP4:
        """
        Get the IMAP connection, reconnecting if necessary.

        Returns:
            Active IMAP4 connection

        Raises:
            BridgeConnectionError: If connection cannot be established
            BridgeAuthenticationError: If authentication fails
        """
        with self._lock:
            if not self.is_connected():
                self.reconnect()

            if not self._connection:
                raise BridgeConnectionError("Connection not established")

            return self._connection

    @property
    def connection(self) -> imaplib.IMAP4:
        """
        Property for accessing the IMAP connection.

        Returns:
            Active IMAP4 connection

        Raises:
            BridgeConnectionError: If connection cannot be established
            BridgeAuthenticationError: If authentication fails
        """
        return self.get_connection()

    def execute_with_retry(
        self, func: Callable[[], Any], max_retries: int = MAX_RECONNECTION_ATTEMPTS
    ) -> Any:
        """
        Execute a function with automatic retry on transient failures.

        Retries with exponential backoff if connection is lost.

        Args:
            func: Function to execute (should use self.get_connection())
            max_retries: Maximum number of retry attempts

        Returns:
            Result of func()

        Raises:
            BridgeConnectionError: If all retries fail
            BridgeAuthenticationError: If authentication fails
            Other exceptions: From func() if not a connection error
        """
        last_exception: Exception | None = None

        for attempt in range(max_retries):
            try:
                return func()
            except (
                ConnectionResetError,
                BrokenPipeError,
                OSError,
                IMAP4Abort,
            ) as e:
                last_exception = e

                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, ...
                    delay = 2**attempt
                    time.sleep(delay)

                    # Try to reconnect
                    with contextlib.suppress(Exception):
                        self.reconnect()

        # All retries failed
        raise BridgeConnectionError(
            f"Operation failed after {max_retries} attempts. Check Bridge connection."
        ) from last_exception
