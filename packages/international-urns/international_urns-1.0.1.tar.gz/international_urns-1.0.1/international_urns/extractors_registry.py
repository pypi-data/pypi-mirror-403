"""Central registry for URN metadata extractors."""

import inspect
import re
from typing import Any, Protocol


class ExtractorFunc(Protocol):
    """Protocol for extractor functions.

    Extractors must accept a URN string and return a dictionary with metadata.
    """

    def __call__(self, urn: str) -> dict[str, Any]: ...


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


class URNExtractorRegistry:
    """Centralized registry for country/document-type specific URN metadata extractors.

    The registry maintains a mapping of (country_code, document_type) tuples to
    extractor functions. Country codes must be ISO 3166-1 Alpha-2 codes.
    """

    def __init__(self) -> None:
        self._extractors: dict[tuple[str, str], ExtractorFunc] = {}

    def register(self, country_code: str, document_type: str, extractor: ExtractorFunc) -> None:
        """Register an extractor for a specific country and document type.

        :param country_code: ISO 3166-1 Alpha-2 country code (case-insensitive)
        :type country_code: str
        :param document_type: Document type identifier (case-insensitive)
        :type document_type: str
        :param extractor: Extractor function that accepts a URN and returns metadata dict
        :type extractor: ExtractorFunc
        :raises ValueError: If country code is invalid or extractor already registered
        :raises TypeError: If extractor is not callable or has wrong signature
        """
        _validate_country_code(country_code)

        # Validate that extractor is callable
        if not callable(extractor):
            raise TypeError(f"Extractor must be callable, got {type(extractor).__name__}")

        # Validate signature: must accept exactly one parameter
        try:
            sig = inspect.signature(extractor)
            params = list(sig.parameters.values())

            if len(params) != 1:
                raise TypeError(
                    f"Extractor must accept exactly one parameter (urn: str), "
                    f"got {len(params)} parameters"
                )
        except (ValueError, TypeError) as e:
            # Some built-in functions don't have inspectable signatures
            # We'll allow them but log a warning
            import warnings

            warnings.warn(
                f"Could not inspect extractor signature for {country_code}:{document_type}: {e}",
                RuntimeWarning,
                stacklevel=2,
            )

        key = (country_code.lower(), document_type.lower())
        if key in self._extractors:
            raise ValueError(f"Extractor already registered for {country_code}:{document_type}")
        self._extractors[key] = extractor

    def get_extractor(self, country_code: str, document_type: str) -> ExtractorFunc | None:
        """Get an extractor for a specific country and document type.

        :param country_code: ISO 3166-1 Alpha-2 country code (case-insensitive)
        :type country_code: str
        :param document_type: Document type identifier (case-insensitive)
        :type document_type: str
        :return: The extractor function, or None if not found
        :rtype: ExtractorFunc | None
        """
        key = (country_code.lower(), document_type.lower())
        return self._extractors.get(key)

    def list_extractors(self) -> list[tuple[str, str]]:
        """List all registered (country_code, document_type) combinations.

        :return: List of tuples containing country codes and document types
        :rtype: list[tuple[str, str]]
        """
        return list(self._extractors.keys())

    def has_extractor(self, country_code: str, document_type: str) -> bool:
        """Check if an extractor exists for the given combination.

        :param country_code: ISO 3166-1 Alpha-2 country code (case-insensitive)
        :type country_code: str
        :param document_type: Document type identifier (case-insensitive)
        :type document_type: str
        :return: True if an extractor is registered, False otherwise
        :rtype: bool
        """
        key = (country_code.lower(), document_type.lower())
        return key in self._extractors


def get_extractor_registry() -> URNExtractorRegistry:
    """Get the current context's URN extractor registry instance.

    This function returns the extractor registry for the current context.
    In normal usage, this returns the default global registry. In isolated
    contexts (e.g., during testing), it returns the context-specific registry.

    :return: The current context's URNExtractorRegistry instance
    :rtype: URNExtractorRegistry
    """
    from international_urns.registry_context import get_registry_context_manager

    manager = get_registry_context_manager()
    context = manager.get_current()
    return context.extractors


__all__ = ["ExtractorFunc", "URNExtractorRegistry", "get_extractor_registry"]
