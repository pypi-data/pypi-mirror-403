"""Central registry for URN validators."""

import inspect
import re
from typing import Protocol


class ValidatorFunc(Protocol):
    """Protocol for validator functions.

    Validators must accept a URN string and return the validated/normalized URN.
    They should raise ValueError or ValidationError on invalid input.
    """

    def __call__(self, urn: str) -> str: ...


def _validate_country_code(country_code: str) -> None:
    """Validate that country code follows ISO 3166-1 Alpha-2 format.

    :param country_code: Country code to validate
    :type country_code: str
    :raises ValueError: If country code is not 2 alphabetic characters or "--"
    """
    if not re.match(r"^([a-zA-Z]{2}|--)$", country_code):
        raise ValueError(
            f"Country code must be ISO 3166-1 Alpha-2 (2 letters) or '--'. Got: {country_code}"
        )


class URNValidatorRegistry:
    """Centralized registry for country/document-type specific URN validators.

    The registry maintains a mapping of (country_code, document_type) tuples to
    validator functions. Country codes must be ISO 3166-1 Alpha-2 codes.
    """

    def __init__(self) -> None:
        self._validators: dict[tuple[str, str], ValidatorFunc] = {}

    def register(self, country_code: str, document_type: str, validator: ValidatorFunc) -> None:
        """Register a validator for a specific country and document type.

        :param country_code: ISO 3166-1 Alpha-2 country code (case-insensitive)
        :type country_code: str
        :param document_type: Document type identifier (case-insensitive)
        :type document_type: str
        :param validator: Validator function that accepts and returns a URN string
        :type validator: ValidatorFunc
        :raises ValueError: If country code is invalid or validator already registered
        :raises TypeError: If validator is not callable or has wrong signature
        """
        _validate_country_code(country_code)

        # Validate that validator is callable
        if not callable(validator):
            raise TypeError(f"Validator must be callable, got {type(validator).__name__}")

        # Validate signature: must accept exactly one parameter
        try:
            sig = inspect.signature(validator)
            params = list(sig.parameters.values())

            if len(params) != 1:
                raise TypeError(
                    f"Validator must accept exactly one parameter (urn: str), "
                    f"got {len(params)} parameters"
                )
        except (ValueError, TypeError) as e:
            # Some built-in functions don't have inspectable signatures
            # We'll allow them but log a warning
            import warnings

            warnings.warn(
                f"Could not inspect validator signature for {country_code}:{document_type}: {e}",
                RuntimeWarning,
                stacklevel=2,
            )

        key = (country_code.lower(), document_type.lower())
        if key in self._validators:
            raise ValueError(f"Validator already registered for {country_code}:{document_type}")
        self._validators[key] = validator

    def get_validator(self, country_code: str, document_type: str) -> ValidatorFunc | None:
        """Get a validator for a specific country and document type.

        :param country_code: ISO 3166-1 Alpha-2 country code (case-insensitive)
        :type country_code: str
        :param document_type: Document type identifier (case-insensitive)
        :type document_type: str
        :return: The validator function, or None if not found
        :rtype: ValidatorFunc | None
        """
        key = (country_code.lower(), document_type.lower())
        return self._validators.get(key)

    def list_validators(self) -> list[tuple[str, str]]:
        """List all registered (country_code, document_type) combinations.

        :return: List of tuples containing country codes and document types
        :rtype: list[tuple[str, str]]
        """
        return list(self._validators.keys())

    def has_validator(self, country_code: str, document_type: str) -> bool:
        """Check if a validator exists for the given combination.

        :param country_code: ISO 3166-1 Alpha-2 country code (case-insensitive)
        :type country_code: str
        :param document_type: Document type identifier (case-insensitive)
        :type document_type: str
        :return: True if a validator is registered, False otherwise
        :rtype: bool
        """
        key = (country_code.lower(), document_type.lower())
        return key in self._validators


def get_validator_registry() -> URNValidatorRegistry:
    """Get the current context's URN validator registry instance.

    This function returns the validator registry for the current context.
    In normal usage, this returns the default global registry. In isolated
    contexts (e.g., during testing), it returns the context-specific registry.

    :return: The current context's URNValidatorRegistry instance
    :rtype: URNValidatorRegistry
    """
    from international_urns.registry_context import get_registry_context_manager

    manager = get_registry_context_manager()
    context = manager.get_current()
    return context.validators


__all__ = ["ValidatorFunc", "URNValidatorRegistry", "get_validator_registry"]
