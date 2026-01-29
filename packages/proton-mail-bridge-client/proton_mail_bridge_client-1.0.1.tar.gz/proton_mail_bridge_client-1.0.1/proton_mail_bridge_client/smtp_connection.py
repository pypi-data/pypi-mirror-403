"""
SMTP connection management for proton-mail-bridge-client.

Handles persistent SMTP connections with automatic reconnection and retry logic.
"""

import contextlib
import smtplib
import ssl
import threading
import time
from collections.abc import Callable
from typing import Any

from .config import MAX_RECONNECTION_ATTEMPTS
from .exceptions import (
    SMTPAuthenticationError,
    SMTPConnectionError,
    SMTPTimeoutError,
)


class SMTPConnectionManager:
    """
    Manages persistent SMTP connection to ProtonMail Bridge.

    Provides automatic reconnection with exponential backoff, connection health
    monitoring, and thread-safe access to the SMTP connection.

    Attributes:
        host: Bridge SMTP host
        port: Bridge SMTP port
        email: ProtonMail email address
        password: Bridge password
        timeout: Connection timeout in seconds
    """

    def __init__(self, host: str, port: int, email: str, password: str, timeout: int = 30):
        """
        Initialize connection manager.

        Args:
            host: Bridge SMTP host (typically 127.0.0.1)
            port: Bridge SMTP port (typically 1025)
            email: ProtonMail email address
            password: Bridge password (NOT ProtonMail account password)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.email = email
        self._password = password  # Private to avoid accidental logging
        self.timeout = timeout

        self._connection: smtplib.SMTP | None = None
        self._lock = threading.RLock()
        self._connected = False

    def connect(self) -> None:
        """
        Establish connection to ProtonMail Bridge.

        Creates SMTP connection, upgrades to TLS with STARTTLS, and authenticates.

        Raises:
            SMTPConnectionError: If connection fails
            SMTPAuthenticationError: If authentication fails
            SMTPTimeoutError: If connection times out
        """
        with self._lock:
            try:
                # Connect to Bridge (no SSL initially, will use STARTTLS)
                self._connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

                # Upgrade to TLS with STARTTLS
                # ProtonMail Bridge uses self-signed certificates, so we need to disable verification
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self._connection.starttls(context=ssl_context)

                # Authenticate
                try:
                    self._connection.login(self.email, self._password)
                except smtplib.SMTPAuthenticationError as e:
                    raise SMTPAuthenticationError(
                        f"Authentication failed for {self.email}. "
                        "Verify you're using the Bridge password (not account password)"
                    ) from e

                self._connected = True

            except TimeoutError as e:
                raise SMTPTimeoutError(
                    f"Connection to Bridge at {self.host}:{self.port} timed out"
                ) from e
            except smtplib.SMTPException as e:
                if not isinstance(e, smtplib.SMTPAuthenticationError):
                    raise SMTPConnectionError(f"SMTP error: {e}") from e
                raise
            except OSError as e:
                raise SMTPConnectionError(
                    f"Cannot connect to Bridge at {self.host}:{self.port}. "
                    "Is ProtonMail Bridge running?"
                ) from e

    def disconnect(self) -> None:
        """
        Cleanly disconnect from Bridge.

        Quits and closes the connection.
        """
        with self._lock:
            if self._connection and self._connected:
                try:
                    self._connection.quit()
                except Exception:  # nosec B110 - cleanup: errors during disconnect are irrelevant
                    # Ignore errors during disconnect
                    pass
                finally:
                    self._connection = None
                    self._connected = False

    def _is_connected_unlocked(self) -> bool:
        """
        Check connection health without acquiring lock.

        Must only be called when lock is already held by caller.

        Returns:
            True if connected, False otherwise
        """
        if not self._connected or not self._connection:
            return False

        # NOOP verifies server is responsive without side effects
        try:
            status, _ = self._connection.noop()
            return status == 250  # SMTP success code
        except Exception:
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """
        Check if connection is established and healthy.

        Returns:
            True if connected, False otherwise
        """
        with self._lock:
            return self._is_connected_unlocked()

    def reconnect(self) -> None:
        """
        Reconnect to Bridge after connection loss.

        Disconnects existing connection and establishes a new one.

        Raises:
            SMTPConnectionError: If reconnection fails
            SMTPAuthenticationError: If authentication fails
        """
        self.disconnect()
        self.connect()

    def get_connection(self) -> smtplib.SMTP:
        """
        Get the SMTP connection, reconnecting if necessary.

        Returns:
            Active SMTP connection

        Raises:
            SMTPConnectionError: If connection cannot be established
            SMTPAuthenticationError: If authentication fails
        """
        with self._lock:
            if not self._is_connected_unlocked():
                # Inline reconnect to avoid lock re-acquisition
                if self._connection and self._connected:
                    with contextlib.suppress(Exception):
                        self._connection.quit()
                    self._connection = None
                    self._connected = False
                self.connect()

            if not self._connection:
                raise SMTPConnectionError("Connection not established")

            return self._connection

    @property
    def connection(self) -> smtplib.SMTP:
        """
        Property for accessing the SMTP connection.

        Returns:
            Active SMTP connection

        Raises:
            SMTPConnectionError: If connection cannot be established
            SMTPAuthenticationError: If authentication fails
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
            SMTPConnectionError: If all retries fail
            SMTPAuthenticationError: If authentication fails
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
                smtplib.SMTPServerDisconnected,
            ) as e:
                # Transient connection errors - retry with exponential backoff
                last_exception = e

                if attempt < max_retries - 1:
                    delay = 2**attempt  # 1s, 2s, 4s, ...
                    time.sleep(delay)

                    with contextlib.suppress(Exception):
                        self.reconnect()

        # All retries failed
        raise SMTPConnectionError(
            f"Operation failed after {max_retries} attempts. Check Bridge connection."
        ) from last_exception

    def __enter__(self) -> "SMTPConnectionManager":
        """Context manager entry - connect to Bridge."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit - disconnect from Bridge."""
        self.disconnect()
