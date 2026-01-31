"""Thread-safe registry context management using contextvars.

This module provides a context-based architecture for managing the three core
registries (validators, generators, extractors) to avoid global state and
enable proper test isolation.
"""

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class RegistryContext:
    """Container for the three registries.

    This class holds instances of all three registry types, allowing them
    to be managed together as a unit for context isolation.
    """

    def __init__(self) -> None:
        """Initialize a new registry context with fresh registry instances."""
        # Import here to avoid circular dependencies
        from international_urns.extractors_registry import URNExtractorRegistry
        from international_urns.generators_registry import URNGeneratorRegistry
        from international_urns.validators_registry import URNValidatorRegistry

        self.validators = URNValidatorRegistry()
        self.generators = URNGeneratorRegistry()
        self.extractors = URNExtractorRegistry()


class RegistryContextManager:
    """Thread-safe context manager for registry access.

    Uses contextvars to provide thread-safe registry access with support
    for isolated contexts (useful for testing). Implements lazy initialization
    to avoid import-time side effects.
    """

    def __init__(self) -> None:
        """Initialize the context manager with a default context."""
        self._context_var: contextvars.ContextVar[RegistryContext] = contextvars.ContextVar(
            "registry_context"
        )
        self._default_context = RegistryContext()
        self._initialized = False

    def get_current(self) -> RegistryContext:
        """Get the current registry context.

        Returns the context-specific registry if one is active (e.g., during
        testing with isolated context), otherwise returns the default context.
        Performs lazy initialization on first access.

        Returns:
            The current RegistryContext instance.
        """
        self.ensure_initialized()
        return self._context_var.get(self._default_context)

    def ensure_initialized(self) -> None:
        """Ensure registries are initialized with built-ins and plugins.

        This method is idempotent - it only performs initialization once,
        no matter how many times it's called. This lazy initialization
        approach avoids import-time side effects.
        """
        if not self._initialized:
            # Import built-ins (triggers auto-registration via __init_subclass__)
            from international_urns import builtin  # noqa: F401

            # Load plugins from entry points
            from international_urns.discovery import load_plugins

            load_plugins()

            self._initialized = True

    @contextmanager
    def isolated(self) -> Iterator[RegistryContext]:
        """Create an isolated registry context.

        This context manager creates a completely fresh set of registries
        that is isolated from the default context. Any registrations made
        within this context will not affect the default registries.

        This is primarily useful for testing, where you want to ensure
        tests don't interfere with each other.

        Yields:
            A fresh RegistryContext instance.

        Example:
            >>> manager = get_registry_context_manager()
            >>> with manager.isolated() as ctx:
            ...     # Use ctx.validators, ctx.generators, ctx.extractors
            ...     # These are completely isolated from the default registries
            ...     pass
        """
        # Create a fresh context
        isolated_context = RegistryContext()

        # Set it as the current context for this context manager
        token = self._context_var.set(isolated_context)

        try:
            yield isolated_context
        finally:
            # Restore the previous context
            self._context_var.reset(token)


# Global singleton instance
_registry_context_manager: RegistryContextManager | None = None


def get_registry_context_manager() -> RegistryContextManager:
    """Get the global registry context manager instance.

    This function returns a singleton instance of RegistryContextManager,
    creating it on first access.

    Returns:
        The global RegistryContextManager instance.
    """
    global _registry_context_manager
    if _registry_context_manager is None:
        _registry_context_manager = RegistryContextManager()
    return _registry_context_manager
