"""
Bridge module that loads the compiled _bindings_ext extension and re-exports its submodules.

The compiled extension is named _bindings_ext to avoid conflicts with this _bindings/ package directory.
This module loads _bindings_ext and registers its submodules so imports like:
    from lumyn_sdk._bindings.connectorx import AnimationBuilder
continue to work.
"""
import sys

# Import the compiled extension module
# Python will find _bindings_ext.*.pyd or _bindings_ext.*.so in the parent directory
from lumyn_sdk import _bindings_ext

# Register the extension module in sys.modules
sys.modules["lumyn_sdk._bindings_ext"] = _bindings_ext

# Get all submodule names from the extension
_submodules = [name for name in dir(_bindings_ext) if not name.startswith('_')]

# Register each submodule so imports like "from lumyn_sdk._bindings.connectorx import X" work
for _name in _submodules:
    _submod = getattr(_bindings_ext, _name)
    # Only register actual submodules (modules, not classes/functions at top level)
    if hasattr(_submod, '__name__'):
        sys.modules[f"lumyn_sdk._bindings.{_name}"] = _submod

# Re-export everything from the extension at the _bindings level
# Use __getattr__ for lazy attribute access instead of import * to avoid double-registration


def __getattr__(name):
    return getattr(_bindings_ext, name)


def __dir__():
    return dir(_bindings_ext)
