"""
Super-LIO: LiDAR-Inertial Odometry with Iceoryx2

This package provides Python bindings for the Super-LIO C++ library,
along with CLI tools for running the LIO and relocation nodes.
"""

__version__ = "2.0.0"

try:
    from ._super_lio_core import (
        SuperLIORunner,
        SuperRelocRunner,
        load_config,
        params,
        set_exit_flag,
        get_exit_flag,
    )
    
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
