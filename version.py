#!/usr/bin/env python3
"""
TimeRing Version Information
"""

VERSION = "1.0.0"
BUILD_DATE = "2025-01-11"
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "pre_release": None
}

def get_version():
    """Get the current version string."""
    return VERSION

def get_version_info():
    """Get detailed version information."""
    return VERSION_INFO.copy()
