"""Constants for the Simforge SDK."""

from importlib.metadata import PackageNotFoundError, version

# Default service URL for Simforge API
DEFAULT_SERVICE_URL = "https://simforge.goharvest.ai"

# Get SDK version from installed package metadata
try:
    __version__ = version("simforge-py")
except PackageNotFoundError:
    __version__ = "unknown"
