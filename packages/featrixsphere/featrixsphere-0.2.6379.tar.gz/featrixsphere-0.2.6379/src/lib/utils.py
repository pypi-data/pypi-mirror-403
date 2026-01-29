#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
import os
import pickle
import logging
import sys
import json
import traceback
import math
from pathlib import Path
from datetime import datetime
from typing import Optional

# load_embedded_space has been moved to featrix.neural.io_utils
# Import it from there for backward compatibility
from featrix.neural.io_utils import load_embedded_space

def convert_to_iso(timestamp: datetime | None) -> str | None:
    if timestamp is None:
        return None
    
    return timestamp.isoformat()


def convert_from_iso(timestamp: str | None) -> datetime | None:
    if timestamp is None:
        return None
    
    return datetime.fromisoformat(timestamp)


def clean_numpy_values(data):
    """
    Recursively clean NaN, Inf, and other non-JSON-serializable values from data.
    Converts them to None which is JSON serializable.
    
    Args:
        data: Data structure to clean (dict, list, or primitive)
        
    Returns:
        Cleaned data structure
    """
    import numpy as np

    if isinstance(data, dict):
        return {k: clean_numpy_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_numpy_values(v) for v in data]
    elif isinstance(data, (float, np.floating)):
        if math.isnan(data) or math.isinf(data):
            return None
        return float(data)  # Convert numpy floats to Python floats
    elif isinstance(data, (int, np.integer)):
        return int(data)  # Convert numpy ints to Python ints
    elif isinstance(data, (bool, np.bool_)):
        return bool(data)  # Convert numpy bools to Python bools
    elif isinstance(data, np.ndarray):
        return clean_numpy_values(data.tolist())  # Convert arrays to lists
    elif data is None or isinstance(data, (str, bool)):
        return data
    else:
        # Handle other numpy types or unknown types
        try:
            # Try to convert to a basic Python type
            if hasattr(data, 'item'):  # numpy scalar
                value = data.item()
                if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    return None
                return value
            else:
                return data
        except:
            # If all else fails, convert to string
            return str(data)

def reset_logger():
    """Removes all handlers and resets logging to default stdout/stderr."""
    logging.getLogger().handlers.clear()  # Remove all handlers
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s [%(levelname)-8s] %(name)-45s: %(message)s")


def validate_user_metadata(user_metadata: Optional[dict], max_size_kb: int = 32) -> Optional[dict]:
    """
    Validate user_metadata size. Returns the metadata if valid, raises ValueError if too large.
    
    Args:
        user_metadata: Dictionary to validate
        max_size_kb: Maximum size in KB (default 32KB)
    
    Returns:
        The validated metadata dict
    
    Raises:
        ValueError: If metadata exceeds max_size_kb when serialized to JSON
    """
    if user_metadata is None:
        return None
    
    if not isinstance(user_metadata, dict):
        raise ValueError(f"user_metadata must be a dict, got {type(user_metadata)}")
    
    # Serialize to JSON to check size
    try:
        json_str = json.dumps(user_metadata)
        size_bytes = len(json_str.encode('utf-8'))
        size_kb = size_bytes / 1024
        
        if size_kb > max_size_kb:
            raise ValueError(
                f"user_metadata exceeds maximum size of {max_size_kb}KB "
                f"(actual: {size_kb:.2f}KB). Please reduce the size of your metadata."
            )
        
        return user_metadata
    except (TypeError, ValueError) as e:
        if isinstance(e, ValueError) and "exceeds maximum size" in str(e):
            raise
        raise ValueError(f"user_metadata must be JSON-serializable: {e}")


def atomic_write_json(filepath: str | Path, data: dict, indent: int = 2, cls=None) -> None:
    """
    Write JSON data to a file atomically.

    Uses write-to-temp-then-rename pattern to prevent readers from seeing
    incomplete/corrupted JSON if they read the file while it's being written.

    Args:
        filepath: Path to the output JSON file
        data: Dictionary to serialize to JSON
        indent: JSON indentation level (default 2, use 0 or None for compact)
        cls: Optional custom JSON encoder class (e.g., NumpyEncoder)
    """
    import tempfile

    filepath = Path(filepath) if isinstance(filepath, str) else filepath
    parent_dir = filepath.parent

    # Ensure parent directory exists
    parent_dir.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory to ensure atomic rename works
    # (rename across filesystems is not atomic)
    fd, tmp_path = tempfile.mkstemp(dir=parent_dir, suffix='.json.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=indent if indent else None, cls=cls)
        # Atomic rename (on same filesystem)
        os.rename(tmp_path, str(filepath))
        # Make file world-readable
        os.chmod(str(filepath), 0o644)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
