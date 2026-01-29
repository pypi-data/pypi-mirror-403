"""
Core engine initialization and management functions.

This module provides functions for initializing and shutting down the
Cersys compute engine, which manages GPU resources and global state.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
from ._bindings import (
    get_lib, check_status, CersysError,
    CS_VERBOSITY_SILENT, CS_VERBOSITY_ERRORS, CS_VERBOSITY_INFO, CS_VERBOSITY_DEBUG,
)

__all__ = [
    "init", "shutdown", "is_initialized", "get_device_info", "get_version",
    "set_verbosity", "VERBOSITY_SILENT", "VERBOSITY_ERRORS", "VERBOSITY_INFO", "VERBOSITY_DEBUG",
    "init_gpu", "find_kernel_file",
]

# Verbosity level constants
VERBOSITY_SILENT = CS_VERBOSITY_SILENT
VERBOSITY_ERRORS = CS_VERBOSITY_ERRORS
VERBOSITY_INFO = CS_VERBOSITY_INFO
VERBOSITY_DEBUG = CS_VERBOSITY_DEBUG

# Kernel file name
_KERNEL_FILENAME = "cersys_kernels.cl"


def find_kernel_file() -> Optional[Path]:
    """
    Find the OpenCL kernel file in standard locations.
    
    Search order:
    1. Same directory as this Python module
    2. Current working directory
    3. src/kernels/ relative to cwd
    4. CERSYS_KERNEL_PATH environment variable
    5. System locations (/usr/local/share/cersys, etc.)
    
    Returns:
        Path to the kernel file if found, None otherwise.
    """
    search_paths = [
        # Same directory as this module (installed with package)
        Path(__file__).parent / _KERNEL_FILENAME,
        # Current working directory
        Path.cwd() / _KERNEL_FILENAME,
        # Source layout
        Path.cwd() / "src" / "kernels" / _KERNEL_FILENAME,
        # Parent directory (for running from subdirs)
        Path.cwd().parent / "src" / "kernels" / _KERNEL_FILENAME,
        # Environment variable
        Path(os.environ.get("CERSYS_KERNEL_PATH", ".")) / _KERNEL_FILENAME,
        # System locations
        Path("/usr/local/share/cersys") / _KERNEL_FILENAME,
        Path("/usr/share/cersys") / _KERNEL_FILENAME,
        Path("/opt/homebrew/share/cersys") / _KERNEL_FILENAME,
    ]
    
    for path in search_paths:
        if path.exists():
            return path.resolve()
    
    return None


def init_gpu(kernel_path: Optional[str] = None) -> None:
    """
    Initialize GPU kernels from the OpenCL kernel file.
    
    This function compiles and caches the GPU kernels. It is called
    automatically by operations that require GPU acceleration.
    
    Args:
        kernel_path: Path to the kernel file. If None, searches standard locations.
    
    Raises:
        CersysError: If kernel file not found or compilation fails.
    """
    lib = get_lib()
    
    if kernel_path is None:
        found = find_kernel_file()
        if found:
            kernel_path = str(found)
    
    if kernel_path:
        status = lib.cs_gpu_init_from_file(kernel_path.encode('utf-8'))
        check_status(status)
    else:
        # Let C code try its own search paths
        status = lib.cs_gpu_init()
        check_status(status)


def init() -> None:
    """
    Initialize the Cersys compute engine.
    
    This function must be called before using any other Cersys functions.
    It initializes the computation context and, if available, sets up
    GPU acceleration via OpenCL.
    
    Note:
        If OpenCL/GPU is not available, the engine automatically falls
        back to CPU mode using optimized BLAS and SIMD operations.
    
    Example:
        >>> import cersys as cs
        >>> cs.init()
        >>> # Use cersys...
        >>> cs.shutdown()
    """
    lib = get_lib()
    status = lib.cs_engine_init()
    check_status(status)


def shutdown() -> None:
    """
    Shutdown the Cersys compute engine.
    
    This function releases all GPU resources and global state.
    Call this when you're done using Cersys to ensure clean cleanup.
    
    Note:
        After calling shutdown(), you must call init() again before
        using other Cersys functions.
    
    Example:
        >>> import cersys as cs
        >>> cs.init()
        >>> # Use cersys...
        >>> cs.shutdown()
    """
    lib = get_lib()
    lib.cs_engine_shutdown()


def is_initialized() -> bool:
    """
    Check if the Cersys engine is currently initialized.
    
    Returns:
        bool: True if the engine is initialized and ready to use.
    
    Example:
        >>> import cersys as cs
        >>> cs.is_initialized()
        False
        >>> cs.init()
        >>> cs.is_initialized()
        True
    """
    lib = get_lib()
    return bool(lib.cs_engine_is_initialized())


def get_device_info() -> Dict[str, Any]:
    """
    Get information about the current compute device.
    
    Returns:
        dict: A dictionary containing:
            - platform (str): Platform name (e.g., "Apple", "CPU")
            - device (str): Device name (e.g., "Apple M2", "CPU (BLAS/SIMD)")
            - memory_gb (float): Global memory in gigabytes (0 for CPU mode)
            - is_gpu (bool): Whether using GPU acceleration
    
    Raises:
        CersysError: If the engine is not initialized.
    
    Example:
        >>> import cersys as cs
        >>> cs.init()
        >>> info = cs.get_device_info()
        >>> if info['is_gpu']:
        ...     print(f"Running on {info['device']} with {info['memory_gb']:.1f} GB")
        ... else:
        ...     print("Running in CPU-only mode")
    """
    lib = get_lib()
    
    if not lib.cs_engine_is_initialized():
        raise CersysError(-1, "Engine not initialized. Call cersys.init() first.")
    
    platform = lib.cs_engine_platform_name()
    device = lib.cs_engine_device_name()
    memory = lib.cs_engine_global_memory()
    
    return {
        "platform": platform.decode('utf-8') if platform else "Unknown",
        "device": device.decode('utf-8') if device else "Unknown",
        "memory_gb": memory / (1024 ** 3),
        "is_gpu": bool(lib.cs_engine_is_gpu()),
    }


def set_verbosity(level: int) -> None:
    """
    Set the verbosity level for library output.
    
    Args:
        level: Verbosity level. Use one of:
            - cs.VERBOSITY_SILENT (0): No output
            - cs.VERBOSITY_ERRORS (1): Only errors
            - cs.VERBOSITY_INFO (2): Errors + startup/shutdown info (default)
            - cs.VERBOSITY_DEBUG (3): All output
    
    Example:
        >>> import cersys as cs
        >>> cs.set_verbosity(cs.VERBOSITY_SILENT)  # Suppress all output
        >>> cs.init()  # No output printed
    """
    lib = get_lib()
    lib.cs_set_verbosity(level)


def get_version() -> str:
    """
    Get the Cersys library version string.
    
    Returns:
        str: Version string in semver format (e.g., "0.0.2").
    
    Example:
        >>> import cersys as cs
        >>> cs.get_version()
        '0.0.2'
    """
    from . import __version__
    return __version__
