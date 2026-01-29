"""
Super-LIO: LiDAR-Inertial Odometry with Iceoryx2

This package provides Python bindings for the Super-LIO C++ library,
along with CLI tools for running the LIO and relocation nodes.
"""

__version__ = "2.0.0"

try:
    import os
    import sys
    
    # Debug: Print environment info
    print(f"DEBUG: Initializing super_lio...", file=sys.stderr)
    print(f"DEBUG: CWD: {os.getcwd()}", file=sys.stderr)
    print(f"DEBUG: PYTHONPATH: {sys.path}", file=sys.stderr)
    
    try:
        print("DEBUG: Attempting to import _super_lio_core...", file=sys.stderr)
        from ._super_lio_core import (
            SuperLIORunner,
            SuperRelocRunner,
            load_config,
            params,
            set_exit_flag,
            get_exit_flag,
        )
        print("DEBUG: Successfully imported _super_lio_core", file=sys.stderr)
    except ImportError as e:
        print(f"DEBUG: Failed to import _super_lio_core: {e}", file=sys.stderr)
        # Try to inspect the .so location
        try:
            import importlib.util
            spec = importlib.util.find_spec(".super_lio._super_lio_core", package="super_lio")
            if spec:
                print(f"DEBUG: Found specloc: {spec.origin}", file=sys.stderr)
                # Try ldd on linux
                if sys.platform.startswith('linux') and spec.origin:
                    print("DEBUG: Running ldd on extension...", file=sys.stderr)
                    os.system(f"ldd {spec.origin}")
        except Exception as  debug_e:
            print(f"DEBUG: Could not debug import failure: {debug_e}", file=sys.stderr)
        raise e
    
    __all__ = [
        "SuperLIORunner",
        "SuperRelocRunner",
        "load_config",
        "params",
        "set_exit_flag",
        "get_exit_flag",
    ]
except ImportError as e:
    import warnings
    warnings.warn(
        f"Failed to import native module: {e}. "
        "The C++ bindings are not available. "
        "Only YAML config utilities will work."
    )
    
    # Provide stubs when native module is not available
    SuperLIORunner = None
    SuperRelocRunner = None
    load_config = None
    params = None
    set_exit_flag = None
    get_exit_flag = None

# Always available: config utilities
from .config import (
    load_yaml,
    save_yaml,
    get_nested,
    set_nested,
    format_yaml,
)

__all__ = [
    "__version__",
    "SuperLIORunner",
    "SuperRelocRunner", 
    "load_config",
    "params",
    "set_exit_flag",
    "get_exit_flag",
    "load_yaml",
    "save_yaml",
    "get_nested",
    "set_nested",
    "format_yaml",
]
