"""
Model I/O and serialization utilities.

This module provides functions for saving and loading models,
as well as exporting to various formats.
"""

from typing import Union, Optional
from pathlib import Path

from ._bindings import (
    get_lib, CS_FORMAT_NATIVE, CS_FORMAT_NUMPY, CS_FORMAT_SAFETENSORS, CS_FORMAT_JSON,
)
from .model import Model
from .tensor import Tensor

__all__ = [
    "save_model", "load_model",
    "export_numpy", "export_safetensors", "export_json_metadata",
    "detect_format",
]


def save_model(model: Model, path: Union[str, Path]) -> None:
    """
    Save a model to file.
    
    Saves in the native Cersys format (.csm) which preserves full
    model configuration and can be loaded back efficiently.
    
    Args:
        model: The model to save.
        path: Output file path.
    
    Example:
        >>> model = cs.MatrixFactorization(1000, 5000, 64)
        >>> # ... train model ...
        >>> cs.save_model(model, "my_model.csm")
    """
    model.save(str(path))


def load_model(path: Union[str, Path]) -> Model:
    """
    Load a model from file.
    
    Args:
        path: Path to a saved model file.
    
    Returns:
        Model: The loaded model.
    
    Note:
        The returned model type is determined by the file contents.
        Currently returns a base Model instance.
    
    Example:
        >>> model = cs.load_model("my_model.csm")
        >>> scores = model.score(user_id=42, item_ids=[1, 2, 3])
    """
    return Model.load(str(path))


def export_numpy(tensor: Tensor, path: Union[str, Path]) -> None:
    """
    Export a tensor to NumPy .npy format.
    
    This allows loading the tensor in any NumPy environment.
    
    Args:
        tensor: The tensor to export.
        path: Output file path (should end with .npy).
    
    Example:
        >>> tensor = cs.rand_uniform((100, 64))
        >>> cs.export_numpy(tensor, "embeddings.npy")
        >>> # Later, in any Python environment:
        >>> import numpy as np
        >>> embeddings = np.load("embeddings.npy")
    """
    tensor.to_npy(str(path))


def export_safetensors(model: Model, path: Union[str, Path]) -> None:
    """
    Export model weights to HuggingFace safetensors format.
    
    This format is compatible with the HuggingFace ecosystem and
    can be loaded in Python, JavaScript, and other languages.
    
    Args:
        model: The model to export.
        path: Output file path (should end with .safetensors).
    
    Example:
        >>> model = cs.MatrixFactorization(1000, 5000, 64)
        >>> cs.export_safetensors(model, "model.safetensors")
        >>> # Load in Python:
        >>> from safetensors import safe_open
        >>> with safe_open("model.safetensors", framework="np") as f:
        ...     user_embeddings = f.get_tensor("mf.user_embeddings")
    """
    model.to_safetensors(str(path))


def export_json_metadata(model: Model, path: Optional[Union[str, Path]] = None) -> str:
    """
    Export model metadata as JSON.
    
    The JSON includes model configuration, dimensions, parameter counts,
    and other metadata useful for documentation or ONNX export.
    
    Args:
        model: The model to export metadata from.
        path: Optional file path. If provided, writes JSON to file.
    
    Returns:
        str: The JSON string.
    
    Example:
        >>> model = cs.MatrixFactorization(1000, 5000, 64)
        >>> metadata = cs.export_json_metadata(model)
        >>> print(metadata)
        {"type": "matrix_factorization", "num_users": 1000, ...}
    """
    json_str = model.metadata_json()
    
    if path is not None:
        with open(str(path), 'w') as f:
            f.write(json_str)
    
    return json_str


def detect_format(path: Union[str, Path]) -> str:
    """
    Detect the format of a model or tensor file.
    
    Args:
        path: Path to the file.
    
    Returns:
        str: Format name ("native", "numpy", "safetensors", "json", or "unknown").
    
    Example:
        >>> fmt = cs.detect_format("model.csm")
        >>> print(fmt)
        native
    """
    lib = get_lib()
    format_code = lib.cs_detect_format(str(path).encode('utf-8'))
    
    format_map = {
        CS_FORMAT_NATIVE: "native",
        CS_FORMAT_NUMPY: "numpy",
        CS_FORMAT_SAFETENSORS: "safetensors",
        CS_FORMAT_JSON: "json",
    }
    
    return format_map.get(format_code, "unknown")
