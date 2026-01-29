#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Featrix Neural Tools

Diagnostic and analysis tools for Featrix neural embedding spaces.
"""

# Lazy imports to avoid path issues when importing as a module
__all__ = ["compare_clusters_main"]


def compare_clusters_main():
    """Entry point for cluster comparison tool."""
    from .compare_clusters import main
    return main()
