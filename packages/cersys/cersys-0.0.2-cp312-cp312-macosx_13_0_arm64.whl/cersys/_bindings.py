"""
Low-level ctypes bindings to the Cersys C library.

This module provides direct access to the C functions via ctypes.
Users should prefer the high-level Python API instead.
"""

import ctypes
from ctypes import (
    c_int, c_uint32, c_uint64, c_float, c_char_p, c_void_p, c_bool,
    POINTER
)
import os
import platform
from pathlib import Path
from typing import Optional

# =============================================================================
# C TYPE ALIASES (matching cs_types.h)
# =============================================================================

# cs_float_t is float (32-bit)
cs_float_t = c_float
cs_float_ptr = POINTER(c_float)

# cs_index_t is uint32_t
cs_index_t = c_uint32

# cs_size_t is size_t (platform dependent)
cs_size_t = ctypes.c_size_t

# cs_id_t is uint32_t  
cs_id_t = c_uint32

# CSStatus is int
CSStatus = c_int

# =============================================================================
# CONSTANTS
# =============================================================================

# Status codes (from cs_error.h)
CS_SUCCESS = 0

# General errors
CS_ERROR_UNKNOWN = 1
CS_ERROR_INVALID_ARGUMENT = 2
CS_ERROR_NULL_POINTER = 3
CS_ERROR_OUT_OF_BOUNDS = 4
CS_ERROR_OVERFLOW = 5

# Memory errors
CS_ERROR_OUT_OF_MEMORY = 100
CS_ERROR_ALLOCATION_FAILED = 101
CS_ERROR_BUFFER_TOO_SMALL = 102
CS_ERROR_ALIGNMENT_FAILED = 103

# Engine/OpenCL errors
CS_ERROR_ENGINE_NOT_INITIALIZED = 200
CS_ERROR_ENGINE_ALREADY_INITIALIZED = 201
CS_ERROR_NO_PLATFORM = 202
CS_ERROR_NO_DEVICE = 203
CS_ERROR_CONTEXT_FAILED = 204
CS_ERROR_QUEUE_FAILED = 205
CS_ERROR_KERNEL_COMPILE_FAILED = 206
CS_ERROR_KERNEL_EXEC_FAILED = 207
CS_ERROR_BUFFER_CREATE_FAILED = 208
CS_ERROR_BUFFER_TRANSFER_FAILED = 209

# Model errors
CS_ERROR_MODEL_INVALID = 300
CS_ERROR_MODEL_NOT_CONFIGURED = 301
CS_ERROR_MODEL_TYPE_MISMATCH = 302
CS_ERROR_LAYER_INVALID = 303
CS_ERROR_DIMENSION_MISMATCH = 304
CS_ERROR_TRAINING_FAILED = 305

# Data errors
CS_ERROR_MATRIX_INVALID = 400
CS_ERROR_SPARSE_FORMAT_INVALID = 401
CS_ERROR_DATA_CORRUPTED = 402

# File/IO errors
CS_ERROR_FILE_OPEN_FAILED = 500
CS_ERROR_FILE_READ_FAILED = 501
CS_ERROR_FILE_WRITE_FAILED = 502
CS_ERROR_VERSION_MISMATCH = 503
CS_ERROR_FORMAT_INVALID = 504


# =============================================================================
# ERROR CONTEXT STRUCT
# =============================================================================

class CSErrorContext(ctypes.Structure):
    _fields_ = [
        ("code", CSStatus),
        ("file", c_char_p),
        ("line", c_int),
        ("message", ctypes.c_char * 256),
    ]

# Model types
CS_MODEL_MATRIX_FACTORIZATION = 0

# Layer types (matching C CSLayerType enum)
CS_LAYER_EMBEDDING = 0
CS_LAYER_DENSE = 1
CS_LAYER_BATCH_NORM = 2
CS_LAYER_LAYER_NORM = 3
CS_LAYER_DROPOUT = 4
CS_LAYER_RELU = 5
CS_LAYER_LEAKY_RELU = 6
CS_LAYER_GELU = 7
CS_LAYER_SIGMOID = 8
CS_LAYER_TANH = 9
CS_LAYER_SOFTMAX = 10

# Activation types (aliases for layer types)
CS_ACTIVATION_RELU = CS_LAYER_RELU
CS_ACTIVATION_SIGMOID = CS_LAYER_SIGMOID
CS_ACTIVATION_TANH = CS_LAYER_TANH
CS_ACTIVATION_LEAKY_RELU = CS_LAYER_LEAKY_RELU
CS_ACTIVATION_GELU = CS_LAYER_GELU
CS_ACTIVATION_SOFTMAX = CS_LAYER_SOFTMAX

# Serialization formats (cs_serialize.h)
CS_FORMAT_UNKNOWN = 0
CS_FORMAT_CSM = 1
CS_FORMAT_NPY = 2
CS_FORMAT_SAFETENSORS = 3
CS_FORMAT_RAW = 4
CS_FORMAT_JSON = 5

# Backwards-compatible aliases
CS_FORMAT_NATIVE = CS_FORMAT_CSM
CS_FORMAT_NUMPY = CS_FORMAT_NPY

# Verbosity levels (from cs_engine.h)
CS_VERBOSITY_SILENT = 0
CS_VERBOSITY_ERRORS = 1
CS_VERBOSITY_INFO = 2
CS_VERBOSITY_DEBUG = 3

# =============================================================================
# OPAQUE HANDLE TYPES
# =============================================================================

# Use void pointers for opaque C structs
CSTensorPtr = c_void_p
CSSparseMatrixPtr = c_void_p
CSModelPtr = c_void_p
CSLayerPtr = c_void_p
CSOptimizerPtr = c_void_p
CSBufferPtr = c_void_p
CSPoolPtr = c_void_p

# =============================================================================
# LIBRARY LOADING
# =============================================================================

_lib: Optional[ctypes.CDLL] = None

def _find_library() -> Path:
    """Find the cersys library in standard locations."""
    # Library name varies by platform
    system = platform.system()
    if system == "Darwin":
        lib_names = ["libcersys.dylib", "libcersys.a"]
    elif system == "Linux":
        lib_names = ["libcersys.so", "libcersys.a"]
    elif system == "Windows":
        lib_names = ["cersys.dll", "libcersys.dll"]
    else:
        lib_names = ["libcersys.so", "libcersys.a"]
    
    # Search paths (in priority order)
    search_paths = [
        # Same directory as this file
        Path(__file__).parent,
        # Package root
        Path(__file__).parent.parent,
        # Repository root (for development)
        Path(__file__).parent.parent.parent,
        # Standard system locations
        Path("/usr/local/lib"),
        Path("/usr/lib"),
        # Environment variable
        Path(os.environ.get("CERSYS_LIB_PATH", ".")),
    ]
    
    for path in search_paths:
        for lib_name in lib_names:
            lib_path = path / lib_name
            if lib_path.exists():
                return lib_path
    
    raise FileNotFoundError(
        f"Could not find cersys library. Searched: {search_paths}\n"
        f"Set CERSYS_LIB_PATH environment variable or build the library first."
    )


def _load_library() -> ctypes.CDLL:
    """Load the shared library and set up function signatures."""
    global _lib
    if _lib is not None:
        return _lib
    
    lib_path = _find_library()
    
    # For static library, we need a small shim. Check for shared first
    if lib_path.suffix in (".a", ".lib"):
        # Can't load static library directly with ctypes
        # Try to find or build a shared version
        shared_path = lib_path.with_suffix(".dylib" if platform.system() == "Darwin" else ".so")
        if not shared_path.exists():
            raise FileNotFoundError(
                f"Found static library at {lib_path}, but need shared library.\n"
                "Run 'make shared' to build libcersys.dylib or libcersys.so"
            )
        lib_path = shared_path
    
    _lib = ctypes.CDLL(str(lib_path))
    _setup_signatures(_lib)
    return _lib


def _setup_signatures(lib: ctypes.CDLL) -> None:
    """Define C function signatures for type safety."""
    
    # =========================================================================
    # Error handling (cs_error.h)
    # =========================================================================
    lib.cs_status_string.argtypes = [CSStatus]
    lib.cs_status_string.restype = c_char_p
    
    lib.cs_get_last_error.argtypes = []
    lib.cs_get_last_error.restype = CSStatus
    
    lib.cs_get_error_context.argtypes = []
    lib.cs_get_error_context.restype = POINTER(CSErrorContext)
    
    lib.cs_clear_error.argtypes = []
    lib.cs_clear_error.restype = None
    
    # =========================================================================
    # Engine (cs_engine.h)
    # =========================================================================
    lib.cs_engine_init.argtypes = []
    lib.cs_engine_init.restype = CSStatus
    
    lib.cs_engine_shutdown.argtypes = []
    lib.cs_engine_shutdown.restype = None
    
    lib.cs_engine_is_initialized.argtypes = []
    lib.cs_engine_is_initialized.restype = c_bool
    
    lib.cs_engine_platform_name.argtypes = []
    lib.cs_engine_platform_name.restype = c_char_p
    
    lib.cs_engine_device_name.argtypes = []
    lib.cs_engine_device_name.restype = c_char_p
    
    lib.cs_engine_global_memory.argtypes = []
    lib.cs_engine_global_memory.restype = cs_size_t

    lib.cs_engine_is_gpu.argtypes = []
    lib.cs_engine_is_gpu.restype = c_bool
    
    lib.cs_set_verbosity.argtypes = [c_int]
    lib.cs_set_verbosity.restype = None
    
    lib.cs_get_verbosity.argtypes = []
    lib.cs_get_verbosity.restype = c_int
    
    # =========================================================================
    # Memory (cs_memory.h)
    # =========================================================================
    lib.cs_malloc_aligned.argtypes = [cs_size_t]
    lib.cs_malloc_aligned.restype = c_void_p
    
    lib.cs_free_aligned.argtypes = [c_void_p]
    lib.cs_free_aligned.restype = None
    
    lib.cs_rng_seed.argtypes = [c_uint64]
    lib.cs_rng_seed.restype = None
    
    lib.cs_rng_uniform.argtypes = []
    lib.cs_rng_uniform.restype = cs_float_t
    
    lib.cs_rng_normal.argtypes = []
    lib.cs_rng_normal.restype = cs_float_t
    
    # =========================================================================
    # Tensors (cs_memory.h)
    # =========================================================================
    lib.cs_tensor_create_1d.argtypes = [cs_index_t]
    lib.cs_tensor_create_1d.restype = CSTensorPtr
    
    lib.cs_tensor_create_2d.argtypes = [cs_index_t, cs_index_t]
    lib.cs_tensor_create_2d.restype = CSTensorPtr
    
    lib.cs_tensor_zeros_2d.argtypes = [cs_index_t, cs_index_t]
    lib.cs_tensor_zeros_2d.restype = CSTensorPtr
    
    lib.cs_tensor_rand_uniform.argtypes = [cs_index_t, cs_index_t, cs_float_t, cs_float_t]
    lib.cs_tensor_rand_uniform.restype = CSTensorPtr
    
    lib.cs_tensor_clone.argtypes = [CSTensorPtr]
    lib.cs_tensor_clone.restype = CSTensorPtr
    
    lib.cs_tensor_release.argtypes = [CSTensorPtr]
    lib.cs_tensor_release.restype = None
    
    lib.cs_tensor_retain.argtypes = [CSTensorPtr]
    lib.cs_tensor_retain.restype = CSTensorPtr
    
    lib.cs_tensor_get_2d.argtypes = [CSTensorPtr, cs_index_t, cs_index_t]
    lib.cs_tensor_get_2d.restype = cs_float_t
    
    lib.cs_tensor_set_2d.argtypes = [CSTensorPtr, cs_index_t, cs_index_t, cs_float_t]
    lib.cs_tensor_set_2d.restype = CSStatus
    
    lib.cs_tensor_row_ptr.argtypes = [CSTensorPtr, cs_index_t]
    lib.cs_tensor_row_ptr.restype = cs_float_ptr
    
    lib.cs_tensor_data.argtypes = [CSTensorPtr]
    lib.cs_tensor_data.restype = cs_float_ptr
    
    lib.cs_tensor_size.argtypes = [CSTensorPtr]
    lib.cs_tensor_size.restype = cs_size_t
    
    lib.cs_tensor_ndim.argtypes = [CSTensorPtr]
    lib.cs_tensor_ndim.restype = cs_index_t
    
    lib.cs_tensor_dim.argtypes = [CSTensorPtr, cs_index_t]
    lib.cs_tensor_dim.restype = cs_index_t
    
    lib.cs_tensor_to_device.argtypes = [CSTensorPtr]
    lib.cs_tensor_to_device.restype = CSStatus
    
    lib.cs_tensor_to_host.argtypes = [CSTensorPtr]
    lib.cs_tensor_to_host.restype = CSStatus
    
    lib.cs_tensor_wrap.argtypes = [cs_float_ptr, cs_index_t, POINTER(cs_index_t)]
    lib.cs_tensor_wrap.restype = CSTensorPtr

    # RNG fill (in-place)
    lib.cs_rng_fill_uniform.argtypes = [CSTensorPtr, cs_float_t, cs_float_t]
    lib.cs_rng_fill_uniform.restype = None
    
    # =========================================================================
    # Sparse matrices
    # =========================================================================
    lib.cs_sparse_create.argtypes = [cs_index_t, cs_index_t, cs_index_t]
    lib.cs_sparse_create.restype = CSSparseMatrixPtr
    
    lib.cs_sparse_release.argtypes = [CSSparseMatrixPtr]
    lib.cs_sparse_release.restype = None
    
    lib.cs_sparse_get.argtypes = [CSSparseMatrixPtr, cs_index_t, cs_index_t]
    lib.cs_sparse_get.restype = cs_float_t
    
    lib.cs_sparse_to_dense.argtypes = [CSSparseMatrixPtr]
    lib.cs_sparse_to_dense.restype = CSTensorPtr
    
    # Direct array access for sparse matrices
    lib.cs_sparse_row_ptr.argtypes = [CSSparseMatrixPtr]
    lib.cs_sparse_row_ptr.restype = POINTER(cs_index_t)
    
    lib.cs_sparse_col_idx.argtypes = [CSSparseMatrixPtr]
    lib.cs_sparse_col_idx.restype = POINTER(cs_index_t)
    
    lib.cs_sparse_values.argtypes = [CSSparseMatrixPtr]
    lib.cs_sparse_values.restype = cs_float_ptr
    
    # Row operations for sparse matrices
    lib.cs_sparse_row_nnz.argtypes = [CSSparseMatrixPtr, cs_index_t]
    lib.cs_sparse_row_nnz.restype = cs_index_t
    
    lib.cs_sparse_get_row.argtypes = [
        CSSparseMatrixPtr,      # matrix
        cs_index_t,             # row
        POINTER(cs_index_t),    # out_cols
        cs_float_ptr,           # out_vals
        POINTER(cs_index_t),    # out_count (output parameter)
    ]
    lib.cs_sparse_get_row.restype = CSStatus
    
    # GPU transfer for sparse matrices
    lib.cs_sparse_to_device.argtypes = [CSSparseMatrixPtr]
    lib.cs_sparse_to_device.restype = CSStatus
    
    # =========================================================================
    # Models (cs_model.h)
    # =========================================================================
    lib.cs_model_mf_create.argtypes = [cs_id_t, cs_id_t, cs_index_t, c_bool]
    lib.cs_model_mf_create.restype = CSModelPtr
    
    lib.cs_model_release.argtypes = [CSModelPtr]
    lib.cs_model_release.restype = None
    
    lib.cs_model_retain.argtypes = [CSModelPtr]
    lib.cs_model_retain.restype = CSModelPtr
    
    lib.cs_model_forward_user.argtypes = [CSModelPtr, POINTER(cs_id_t), cs_index_t]
    lib.cs_model_forward_user.restype = CSTensorPtr
    
    lib.cs_model_forward_item.argtypes = [CSModelPtr, POINTER(cs_id_t), cs_index_t]
    lib.cs_model_forward_item.restype = CSTensorPtr
    
    # Raw embedding lookup (for side features integration)
    lib.cs_model_lookup_user_embeddings.argtypes = [CSModelPtr, POINTER(cs_id_t), cs_index_t]
    lib.cs_model_lookup_user_embeddings.restype = CSTensorPtr
    
    lib.cs_model_lookup_item_embeddings.argtypes = [CSModelPtr, POINTER(cs_id_t), cs_index_t]
    lib.cs_model_lookup_item_embeddings.restype = CSTensorPtr
    
    lib.cs_model_score.argtypes = [CSModelPtr, POINTER(cs_id_t), POINTER(cs_id_t), cs_index_t]
    lib.cs_model_score.restype = CSTensorPtr  # Returns a tensor
    
    # Fast top-k recommendations using BLAS sgemv
    lib.cs_recommend.argtypes = [CSModelPtr, cs_id_t, cs_index_t, POINTER(cs_id_t), cs_float_ptr]
    lib.cs_recommend.restype = CSStatus
    
    # Fast batch scoring: score a single user against multiple items
    lib.cs_model_score_items.argtypes = [CSModelPtr, cs_id_t, POINTER(cs_id_t), cs_index_t, cs_float_ptr]
    lib.cs_model_score_items.restype = CSStatus
    
    lib.cs_model_train.argtypes = [CSModelPtr]
    lib.cs_model_train.restype = None  # void function
    
    lib.cs_model_eval.argtypes = [CSModelPtr]
    lib.cs_model_eval.restype = None  # void function
    
    lib.cs_model_num_parameters.argtypes = [CSModelPtr]
    lib.cs_model_num_parameters.restype = cs_size_t
    
    # =========================================================================
    # Training (cs_train.h)
    # =========================================================================
    lib.cs_model_train_step_bpr.argtypes = [
        CSModelPtr, 
        POINTER(cs_id_t), POINTER(cs_id_t), POINTER(cs_id_t),
        cs_index_t, cs_float_t, cs_float_t
    ]
    lib.cs_model_train_step_bpr.restype = CSStatus
    
    # ALS training for Matrix Factorization
    lib.cs_model_train_als_epoch.argtypes = [
        CSModelPtr,           # model
        CSSparseMatrixPtr,    # interactions (CSR sparse matrix)
        cs_float_t,           # alpha (confidence weight)
        cs_float_t,           # regularization
        cs_index_t            # num_threads
    ]
    lib.cs_model_train_als_epoch.restype = CSStatus
    
    lib.cs_sample_negatives_uniform.argtypes = [
        CSSparseMatrixPtr,      # interactions (can be NULL)
        POINTER(cs_id_t),       # user_ids
        POINTER(cs_id_t),       # out_neg_items
        cs_index_t,             # batch_size
        cs_index_t,             # num_items
    ]
    lib.cs_sample_negatives_uniform.restype = None  # void function
    
    # =========================================================================
    # Serialization (cs_serialize.h)
    # =========================================================================
    lib.cs_model_save.argtypes = [CSModelPtr, c_char_p]
    lib.cs_model_save.restype = CSStatus
    
    lib.cs_model_load.argtypes = [c_char_p]
    lib.cs_model_load.restype = CSModelPtr
    
    lib.cs_tensor_save.argtypes = [CSTensorPtr, c_char_p, c_char_p]
    lib.cs_tensor_save.restype = CSStatus
    
    lib.cs_tensor_load.argtypes = [c_char_p]
    lib.cs_tensor_load.restype = CSTensorPtr
    
    lib.cs_tensor_to_npy.argtypes = [CSTensorPtr, c_char_p]
    lib.cs_tensor_to_npy.restype = CSStatus
    
    lib.cs_model_to_safetensors.argtypes = [CSModelPtr, c_char_p]
    lib.cs_model_to_safetensors.restype = CSStatus
    
    lib.cs_model_metadata_json.argtypes = [CSModelPtr, c_char_p]
    lib.cs_model_metadata_json.restype = CSStatus
    
    lib.cs_detect_format.argtypes = [c_char_p]
    lib.cs_detect_format.restype = c_int
    
    # =========================================================================
    # GPU kernels (cs_gpu.h)
    # =========================================================================
    lib.cs_gpu_init.argtypes = []
    lib.cs_gpu_init.restype = CSStatus
    
    lib.cs_gpu_init_from_file.argtypes = [c_char_p]
    lib.cs_gpu_init_from_file.restype = CSStatus
    
    lib.cs_gpu_is_ready.argtypes = []
    lib.cs_gpu_is_ready.restype = c_bool
    
    lib.cs_gpu_relu.argtypes = [CSTensorPtr, CSTensorPtr, cs_size_t]
    lib.cs_gpu_relu.restype = CSStatus
    
    lib.cs_gpu_sigmoid.argtypes = [CSTensorPtr, CSTensorPtr, cs_size_t]
    lib.cs_gpu_sigmoid.restype = CSStatus


def get_lib() -> ctypes.CDLL:
    """Get the loaded library, loading it if necessary."""
    return _load_library()


class CersysError(Exception):
    """Exception raised for Cersys library errors."""
    
    def __init__(self, status: int, context: Optional[str] = None):
        self.status = status
        self.context = context
        lib = get_lib()
        status_str = lib.cs_status_string(status).decode('utf-8')
        message = f"Cersys error {status}: {status_str}"
        if context:
            message += f" - {context}"
        super().__init__(message)


def check_status(status: int) -> None:
    """Check a status code and raise an exception if it indicates an error."""
    if status != CS_SUCCESS:
        lib = get_lib()
        ctx = lib.cs_get_error_context()
        context = None
        if ctx:
            ctx = ctx.contents
            msg = ctx.message.decode('utf-8', errors='ignore').strip() if ctx.message else ""
            file_str = ctx.file.decode('utf-8', errors='ignore') if ctx.file else ""
            if file_str and ctx.line:
                context = f"{file_str}:{ctx.line}"
                if msg:
                    context = f"{context} - {msg}"
            elif msg:
                context = msg
        raise CersysError(status, context)
