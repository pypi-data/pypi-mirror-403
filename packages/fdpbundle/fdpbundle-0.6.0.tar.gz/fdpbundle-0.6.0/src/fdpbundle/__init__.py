"""FDP Bundle CLI - Tool for managing FDP Workflow Engine bundles."""

__version__ = "0.6.0"
__author__ = "Hocbt"

from .client import BundleClient

__all__ = ["BundleClient", "__version__"]
