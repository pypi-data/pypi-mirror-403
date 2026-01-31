"""Utilities for accessing package resources (data files like JSON)."""

import sys
import json
from pathlib import Path

if sys.version_info >= (3, 9):
    from importlib.resources import files, as_file
else:
    from importlib_resources import files, as_file


def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource file in the package.
    
    Works both when installed as a wheel and when running locally.
    
    Args:
        relative_path: Path relative to package root, e.g., "utils/homoglyphs/intentional.json"
    
    Returns:
        Path object pointing to the resource file
    """
    # Get the 'utils' package
    utils_files = files("utils")
    
    # Navigate to the requested resource
    for part in relative_path.split("/"):
        utils_files = utils_files / part
    
    # Use as_file context manager to get actual filesystem path
    # This handles both wheel installations and local development
    with as_file(utils_files) as path:
        return path


def load_json_resource(relative_path: str) -> dict:
    """
    Load a JSON file from package resources.
    
    Works both when installed as a wheel and when running locally.
    
    Args:
        relative_path: Path relative to package root, e.g., "homoglyphs/intentional.json"
    
    Returns:
        Parsed JSON content as a dictionary
    """
    path = get_resource_path(relative_path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
