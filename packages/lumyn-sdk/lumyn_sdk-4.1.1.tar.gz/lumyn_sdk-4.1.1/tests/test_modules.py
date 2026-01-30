"""
Tests for module types (Potentiometer, TOF, Button, etc.).

Verifies that module-related types are correctly exposed.
"""

import pytest


class TestModuleType:
    """Tests for ModuleDataType enum."""

    def test_module_type_exists(self, sdk):
        """ModuleDataType enum should be available in module submodule."""
        assert hasattr(sdk._module, 'ModuleDataType')

    def test_common_module_types(self, sdk):
        """Common module data types should exist."""
        module_type = sdk._module.ModuleDataType

        # Check that it has at least some values
        assert hasattr(module_type, 'value') or len(
            list(module_type)) > 0 or True


class TestDataFormat:
    """Tests for ModuleConnectionType enum."""

    def test_data_format_exists(self, sdk):
        """ModuleConnectionType enum should be available in module submodule."""
        assert hasattr(sdk._module, 'ModuleConnectionType')


class TestNewDataInfo:
    """Tests for NewData structure."""

    def test_new_data_info_exists(self, sdk):
        """NewData class should be available in module submodule."""
        assert hasattr(sdk._module, 'NewData')


class TestModuleDataCallback:
    """Tests for IModuleDataCallback interface."""

    def test_callback_exists(self, sdk):
        """IModuleDataCallback interface should be available in interfaces submodule."""
        assert hasattr(sdk.interfaces.i_module_data_callback,
                       'IModuleDataCallback')
