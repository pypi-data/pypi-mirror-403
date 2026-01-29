"""FDP Bundle CLI - Tool for managing FDP Workflow Engine bundles."""

__version__ = "0.4.0"
__author__ = "Data Team"

from .client import BundleClient

__all__ = ["BundleClient", "__version__"]
