"""
Cersys - High-Performance Recommender Systems Library

A production-ready recommender systems library with GPU acceleration,
efficient matrix factorization, and deep learning capabilities.

Example:
    >>> import cersys as cs
    >>> cs.init()
    >>> model = cs.MatrixFactorization(num_users=1000, num_items=5000, embedding_dim=64)
    >>> model.fit(user_ids, item_ids, epochs=10)
    >>> recommendations = model.recommend(user_id=42, top_k=10)
    >>> cs.shutdown()

For more information, visit: https://github.com/22cav/cersys
"""

from .core import (
    init,
    shutdown,
    is_initialized,
    get_device_info,
    get_version,
    set_verbosity,
    init_gpu,
    find_kernel_file,
    VERBOSITY_SILENT,
    VERBOSITY_ERRORS,
    VERBOSITY_INFO,
    VERBOSITY_DEBUG,
)

from .tensor import Tensor, zeros, ones, rand_uniform, rand_normal

from .model import (
    Model,
    MatrixFactorization,
)

from .training import (
    Optimizer,
    SGD,
    Adam,
    AdamW,
    BPRLoss,
    MSELoss,
    ContrastiveLoss,
)

from .sparse import SparseMatrix

from .io import (
    save_model,
    load_model,
    export_numpy,
    export_safetensors,
    export_json_metadata,
    detect_format,
)

from .utils import (
    set_seed,
    sample_negatives,
)

__version__ = "0.0.2"
__author__ = "Matteo Caviglia" 

__all__ = [
    # Core
    "init",
    "shutdown", 
    "is_initialized",
    "get_device_info",
    "get_version",
    "set_verbosity",
    "init_gpu",
    "find_kernel_file",
    "VERBOSITY_SILENT",
    "VERBOSITY_ERRORS",
    "VERBOSITY_INFO",
    "VERBOSITY_DEBUG",
    
    # Tensor
    "Tensor",
    "zeros",
    "ones",
    "rand_uniform",
    "rand_normal",
    
    # Models
    "Model",
    "MatrixFactorization",
    
    # Training
    "Optimizer",
    "SGD",
    "Adam",
    "AdamW",
    "BPRLoss",
    "MSELoss",
    "ContrastiveLoss",
    
    # Sparse
    "SparseMatrix",
    
    # I/O
    "save_model",
    "load_model",
    "export_numpy",
    "export_safetensors",
    "export_json_metadata",
    "detect_format",
    
    # Utils
    "set_seed",
    "sample_negatives",
]
