"""languagechange package initialization."""

from importlib import metadata

try:
    __version__ = metadata.version("languagechange")
except metadata.PackageNotFoundError:
    # Fallback when running from a source checkout
    __version__ = "0.1.0"

__all__ = ["__version__"]
