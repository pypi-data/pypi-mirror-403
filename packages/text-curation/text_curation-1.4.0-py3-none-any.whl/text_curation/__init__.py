from importlib.metadata import version

# Import profiles eagerly so they self-register with the global registry.
# This ensures profile resolution works without requiring manual imports.
import text_curation.profiles  # noqa: F401

from .curator import TextCurator

# Package version as published on PyPI
__version__ = version("text_curation")

# Public API surface
__all__ = ["TextCurator", "__version__"]