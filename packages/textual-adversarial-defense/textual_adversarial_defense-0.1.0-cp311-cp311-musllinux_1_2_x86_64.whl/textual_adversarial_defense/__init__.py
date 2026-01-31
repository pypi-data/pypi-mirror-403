"""Textual Adversarial Defense - Unicode-based attacks and defenses for text models."""

import os
from pathlib import Path

__version__ = "0.1.0"

# Set up the resource path for C++ modules
# This allows C++ code to find JSON resources in both wheel and local installations
try:
    import importlib.resources

    if hasattr(importlib.resources, "files"):
        # Python 3.9+
        utils_path = importlib.resources.files("utils")
        with importlib.resources.as_file(utils_path) as path:
            os.environ["TEXTUAL_DEFENSE_RESOURCES"] = str(path)
except (ImportError, AttributeError, TypeError):
    # Fallback for local development or older Python
    current_dir = Path(__file__).parent.parent.parent
    utils_dir = current_dir / "utils"
    if utils_dir.exists():
        os.environ["TEXTUAL_DEFENSE_RESOURCES"] = str(utils_dir)

try:
    from . import _pipeline
except Exception as e:
    raise ImportError("Failed to import textual_adversarial_defense._pipeline. ") from e

__all__ = ["_pipeline"]
