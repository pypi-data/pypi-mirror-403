"""Input sanitization and validation utilities.

This module provides utilities for sanitizing URN strings before including them
in log messages (preventing log injection attacks) and validating plugin-provided
metadata to prevent code injection and other security issues.
"""

from typing import Any


class InputSanitizer:
    """Provides methods for sanitizing and validating untrusted input.

    This class contains static methods for sanitizing URN strings before
    including them in error messages (to prevent log injection) and for
    validating plugin-provided metadata structures.
    """

    # Maximum allowed URN length to prevent DoS attacks
    MAX_URN_LENGTH = 1024

    # Characters allowed in URN strings per RFC 8141
    # (simplified - actual RFC is more complex, but this is safe)
    ALLOWED_URN_CHARS = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~:/?#[]@!$&'()*+,;=%"
    )

    @classmethod
    def sanitize_for_logging(cls, urn: Any) -> str:
        """Sanitize a URN string for safe inclusion in log messages.

        This method removes control characters, newlines, and other characters
        that could be used for log injection attacks. It also truncates overly
        long strings to prevent DoS attacks.

        Args:
            urn: The URN string to sanitize. If not a string, returns a
                placeholder message.

        Returns:
            A sanitized version of the URN string that is safe to include
            in log messages and error strings.

        Example:
            >>> InputSanitizer.sanitize_for_logging('urn:xx:test:value\\nMALICIOUS')
            'urn:xx:test:value\\x0aMALICIOUS'
        """
        # Handle non-string input
        if not isinstance(urn, str):
            return f"<non-string-value type={type(urn).__name__}>"

        # Truncate overly long strings
        if len(urn) > cls.MAX_URN_LENGTH:
            urn = urn[: cls.MAX_URN_LENGTH] + "...[truncated]"

        # Escape control characters and unprintable characters
        sanitized = "".join(
            char if char.isprintable() and char not in "\n\r\t\x0b\x0c" else f"\\x{ord(char):02x}"
            for char in urn
        )

        return sanitized

    @classmethod
    def validate_metadata(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        """Validate plugin-provided metadata structure.

        This method ensures that metadata provided by plugins contains only
        safe data types (strings, numbers, booleans, None, and lists/dicts
        of these types). It rejects functions, objects, and other potentially
        dangerous types that could be used for code injection.

        Args:
            metadata: The metadata dictionary to validate.

        Returns:
            The validated metadata dictionary (same as input if valid).

        Raises:
            TypeError: If the metadata contains invalid types.
            ValueError: If the metadata structure is invalid.

        Example:
            >>> InputSanitizer.validate_metadata({'country': 'ES', 'type': 'DNI'})
            {'country': 'ES', 'type': 'DNI'}
        """
        if not isinstance(metadata, dict):
            raise TypeError(f"Metadata must be a dictionary, got {type(metadata).__name__}")

        # Validate each key-value pair
        for key, value in metadata.items():
            # Keys must be strings
            if not isinstance(key, str):
                raise TypeError(f"Metadata keys must be strings, got {type(key).__name__}")

            # Validate value type
            cls._validate_metadata_value(value, path=key)

        return metadata

    @classmethod
    def _validate_metadata_value(cls, value: Any, path: str) -> None:
        """Validate a single metadata value recursively.

        Args:
            value: The value to validate.
            path: The path to this value (for error messages).

        Raises:
            TypeError: If the value is not an allowed type.
        """
        # Allowed primitive types
        if value is None or isinstance(value, (str, int, float, bool)):
            return

        # Recursively validate lists
        if isinstance(value, list):
            for i, item in enumerate(value):
                cls._validate_metadata_value(item, path=f"{path}[{i}]")
            return

        # Recursively validate dicts
        if isinstance(value, dict):
            for key, val in value.items():
                if not isinstance(key, str):
                    raise TypeError(
                        f"Dictionary keys must be strings at {path}, got {type(key).__name__}"
                    )
                cls._validate_metadata_value(val, path=f"{path}.{key}")
            return

        # Reject all other types (functions, objects, etc.)
        raise TypeError(
            f"Invalid metadata type at {path}: {type(value).__name__}. "
            f"Only str, int, float, bool, None, list, and dict are allowed."
        )

    @classmethod
    def validate_urn_format(cls, urn: str) -> None:
        """Validate that a URN string doesn't contain suspicious characters.

        This is a basic sanity check to catch obviously malicious input.
        It doesn't validate RFC 8141 compliance (that's the job of urnparse),
        but it does reject strings that are clearly not valid URNs.

        Args:
            urn: The URN string to validate.

        Raises:
            ValueError: If the URN contains suspicious characters.

        Example:
            >>> InputSanitizer.validate_urn_format('urn:xx:test:value')
            >>> InputSanitizer.validate_urn_format('urn:xx:test:\\x00malicious')
            Traceback (most recent call last):
                ...
            ValueError: URN contains invalid characters
        """
        if not isinstance(urn, str):
            raise TypeError(f"URN must be a string, got {type(urn).__name__}")

        # Check length
        if len(urn) > cls.MAX_URN_LENGTH:
            raise ValueError(f"URN exceeds maximum length of {cls.MAX_URN_LENGTH} characters")

        # Check for null bytes (common injection technique)
        if "\x00" in urn:
            raise ValueError("URN contains null bytes")

        # Check for obviously suspicious characters
        for char in urn:
            if not char.isprintable():
                raise ValueError(f"URN contains non-printable character: \\x{ord(char):02x}")
