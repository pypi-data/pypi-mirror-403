#!/usr/bin/env python3
"""
List available loss function versions.

Usage:
    python -m featrix.neural.loss_functions.list_versions

Or from shell:
    python src/lib/featrix/neural/loss_functions/list_versions.py
"""

import os
import sys
import importlib
from pathlib import Path


def get_available_versions():
    """Return list of available loss function version names."""
    loss_functions_dir = Path(__file__).parent
    versions = []

    for f in loss_functions_dir.glob("loss_functions_*.py"):
        # Extract version name without .py extension
        version_name = f.stem  # e.g., "loss_functions_01Jan2026"
        versions.append(version_name)

    return sorted(versions)


def get_version_info(version_name: str) -> dict:
    """Get info about a specific version by importing its module."""
    try:
        # Try importing from package
        module = importlib.import_module(f"featrix.neural.loss_functions.{version_name}")
    except ImportError:
        # Fall back to direct import
        import importlib.util as imp_util
        loss_functions_dir = Path(__file__).parent
        module_path = loss_functions_dir / f"{version_name}.py"
        if not module_path.exists():
            return {"error": f"Version {version_name} not found"}

        spec = imp_util.spec_from_file_location(version_name, module_path)
        module = imp_util.module_from_spec(spec)
        spec.loader.exec_module(module)

    # Extract docstring
    docstring = module.__doc__ or "No description available"

    # Get available loss types
    if hasattr(module, 'LossFramework') and hasattr(module.LossFramework, 'LOSS_TYPES'):
        loss_types = list(module.LossFramework.LOSS_TYPES.keys())
    else:
        loss_types = []

    return {
        "name": version_name,
        "docstring": docstring.strip(),
        "loss_types": loss_types,
    }


def print_versions(detailed=False):
    """Print available versions to stdout."""
    versions = get_available_versions()

    if not versions:
        print("No loss function versions found.")
        return

    print("Available loss function versions:")
    print("=" * 60)

    for version in versions:
        print(f"\n  {version}")

        if detailed:
            info = get_version_info(version)
            if "error" not in info:
                # Print first line of docstring
                first_line = info["docstring"].split("\n")[0]
                print(f"    {first_line}")
                if info["loss_types"]:
                    print(f"    Losses: {', '.join(info['loss_types'])}")

    print("\n" + "=" * 60)
    print("\nUsage:")
    print("  --loss-functions=loss_functions_01Jan2026")
    print("  --loss-functions=loss_functions_21Jan2026")


if __name__ == "__main__":
    detailed = "--detailed" in sys.argv or "-d" in sys.argv
    print_versions(detailed=detailed)
