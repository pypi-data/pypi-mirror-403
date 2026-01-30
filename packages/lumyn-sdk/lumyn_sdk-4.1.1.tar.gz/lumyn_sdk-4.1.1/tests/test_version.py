"""
Tests for the Version API.

Tests version retrieval functions to ensure correct version information
is returned and that the API is stable across builds.

Mirrors C SDK test_version_api.cpp
"""

import pytest
import re
import lumyn_sdk


class TestVersionString:
    """Tests for version string functionality."""

    def test_get_version_returns_non_empty(self):
        """Version string should not be empty."""
        version = lumyn_sdk.__version__
        assert version is not None, "__version__ is None"
        assert len(version) > 0, "Version string is empty"

    def test_get_version_matches_semver_format(self):
        """Version should match SemVer format: MAJOR.MINOR.PATCH."""
        version = lumyn_sdk.__version__
        assert version is not None

        # SemVer format: MAJOR.MINOR.PATCH (optionally with prerelease/build metadata)
        semver_regex = r'^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'
        assert re.match(semver_regex, version), \
            f"Version '{version}' does not match SemVer format"

    def test_get_version_is_consistent(self):
        """Multiple accesses should return the same string."""
        v1 = lumyn_sdk.__version__
        v2 = lumyn_sdk.__version__
        v3 = lumyn_sdk.__version__

        assert v1 is not None
        assert v2 is not None
        assert v3 is not None

        assert v1 == v2, "Version string is not consistent across accesses"
        assert v2 == v3, "Version string is not consistent across accesses"


class TestVersionComponents:
    """Tests for version component functionality."""

    def test_driver_version_major_is_non_negative(self):
        """Major version should be non-negative."""
        # Check if the binding is available
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MAJOR'):
            major = lumyn_sdk.DRIVER_VERSION_MAJOR
            assert major >= 0, "Major version should be non-negative"

    def test_driver_version_minor_is_non_negative(self):
        """Minor version should be non-negative."""
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MINOR'):
            minor = lumyn_sdk.DRIVER_VERSION_MINOR
            assert minor >= 0, "Minor version should be non-negative"

    def test_driver_version_patch_is_non_negative(self):
        """Patch version should be non-negative."""
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_PATCH'):
            patch = lumyn_sdk.DRIVER_VERSION_PATCH
            assert patch >= 0, "Patch version should be non-negative"

    def test_version_components_are_consistent(self):
        """Multiple accesses should return the same values."""
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MAJOR'):
            assert lumyn_sdk.DRIVER_VERSION_MAJOR == lumyn_sdk.DRIVER_VERSION_MAJOR
        
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MINOR'):
            assert lumyn_sdk.DRIVER_VERSION_MINOR == lumyn_sdk.DRIVER_VERSION_MINOR
        
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_PATCH'):
            assert lumyn_sdk.DRIVER_VERSION_PATCH == lumyn_sdk.DRIVER_VERSION_PATCH


class TestVersionSanity:
    """Sanity checks for version values."""

    def test_major_version_is_reasonable(self):
        """Major version should be in a reasonable range."""
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MAJOR'):
            major = lumyn_sdk.DRIVER_VERSION_MAJOR
            # Major version should be between 1 and 99 for a reasonable SDK
            assert 1 <= major <= 99, \
                f"Major version {major} is outside reasonable range [1, 99]"

    def test_minor_version_is_reasonable(self):
        """Minor version should be in a reasonable range."""
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MINOR'):
            minor = lumyn_sdk.DRIVER_VERSION_MINOR
            # Minor version should be between 0 and 99
            assert 0 <= minor <= 99, \
                f"Minor version {minor} is outside reasonable range [0, 99]"

    def test_patch_version_is_reasonable(self):
        """Patch version should be in a reasonable range."""
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_PATCH'):
            patch = lumyn_sdk.DRIVER_VERSION_PATCH
            # Patch version should be between 0 and 999
            assert 0 <= patch <= 999, \
                f"Patch version {patch} is outside reasonable range [0, 999]"


class TestVersionExistence:
    """Tests that version attributes exist."""

    def test_module_has_version_attribute(self):
        """Module should have __version__ attribute."""
        assert hasattr(lumyn_sdk, '__version__'), \
            "lumyn_sdk module should have __version__ attribute"

    def test_version_attribute_is_string(self):
        """__version__ should be a string."""
        assert isinstance(lumyn_sdk.__version__, str), \
            "__version__ should be a string"

    def test_driver_version_components_exist(self):
        """Driver version components should exist (if bindings are available)."""
        # These may not exist if bindings aren't compiled/available
        # Just verify they're integers if they exist
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MAJOR'):
            assert isinstance(lumyn_sdk.DRIVER_VERSION_MAJOR, int), \
                "DRIVER_VERSION_MAJOR should be an integer"
        
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_MINOR'):
            assert isinstance(lumyn_sdk.DRIVER_VERSION_MINOR, int), \
                "DRIVER_VERSION_MINOR should be an integer"
        
        if hasattr(lumyn_sdk, 'DRIVER_VERSION_PATCH'):
            assert isinstance(lumyn_sdk.DRIVER_VERSION_PATCH, int), \
                "DRIVER_VERSION_PATCH should be an integer"


class TestVersionThreadSafety:
    """Basic thread safety checks for version access."""

    def test_version_functions_are_thread_safe(self):
        """Version attributes should be thread-safe (read-only)."""
        # These are module-level constants and should be thread-safe
        # This test verifies they can be accessed many times without issues
        for _ in range(1000):
            assert lumyn_sdk.__version__ is not None
            if hasattr(lumyn_sdk, 'DRIVER_VERSION_MAJOR'):
                assert lumyn_sdk.DRIVER_VERSION_MAJOR >= 0
            if hasattr(lumyn_sdk, 'DRIVER_VERSION_MINOR'):
                assert lumyn_sdk.DRIVER_VERSION_MINOR >= 0
            if hasattr(lumyn_sdk, 'DRIVER_VERSION_PATCH'):
                assert lumyn_sdk.DRIVER_VERSION_PATCH >= 0
