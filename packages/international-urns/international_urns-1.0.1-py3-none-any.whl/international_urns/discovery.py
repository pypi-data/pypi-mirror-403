"""Plugin discovery system using entry points."""

import logging
import warnings
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


def load_plugins() -> None:
    """Load all registered URN validator plugins.

    Plugins should register themselves using the 'international_urns.plugins'
    entry point group in their pyproject.toml::

        [project.entry-points.'international_urns.plugins']
        es = 'international_urns_es'

    When the plugin module is imported, validators should self-register
    using the URNValidator base class and __init_subclass__.
    """
    plugin_entries = entry_points(group="international_urns.plugins")

    for entry_point in plugin_entries:
        try:
            entry_point.load()
        except (ImportError, ModuleNotFoundError) as e:
            # Expected error - module not found or import failed
            warnings.warn(
                f"Failed to import plugin '{entry_point.name}': {e}", RuntimeWarning, stacklevel=2
            )
        except Exception as e:
            # Unexpected error during plugin loading - log with full traceback
            logger.error(
                f"Unexpected error loading plugin '{entry_point.name}': {e}", exc_info=True
            )
            warnings.warn(
                f"Unexpected error loading plugin '{entry_point.name}': {e}",
                RuntimeWarning,
                stacklevel=2,
            )


__all__ = ["load_plugins"]
