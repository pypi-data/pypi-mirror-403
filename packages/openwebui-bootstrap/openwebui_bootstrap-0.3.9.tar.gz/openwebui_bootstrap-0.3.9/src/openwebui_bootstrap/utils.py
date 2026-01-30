"""Utility functions for Open WebUI Bootstrap."""

import importlib.resources
from pathlib import Path


def get_resource_path(resource_name: str) -> str:
    """Get the path to a package resource file.

    Args:
        resource_name: Name of the resource file (e.g., "webui-0.7.2.db")

    Returns:
        Absolute path to the resource file

    Raises:
        FileNotFoundError: If the resource file cannot be found
        ImportError: If the package cannot be located
    """
    try:
        # Get the resource as a path
        resource_ref = (
            importlib.resources.files("openwebui_bootstrap.resources") / resource_name
        )

        # For Python 3.9+, we need to handle the resource path properly
        if hasattr(resource_ref, "resolve"):
            # This is a Path object (Python 3.9+)
            return str(resource_ref.resolve())
        else:
            # Fallback for older versions or different implementations
            with importlib.resources.as_file(resource_ref) as path:
                return str(path)
    except (FileNotFoundError, ImportError) as e:
        raise FileNotFoundError(
            f"Resource {resource_name} not found in openwebui_bootstrap.resources"
        ) from e
