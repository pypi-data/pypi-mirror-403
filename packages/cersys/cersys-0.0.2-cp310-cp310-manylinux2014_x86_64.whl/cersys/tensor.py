"""
Tensor class and tensor creation utilities.

Tensors are the fundamental data structure in Cersys, representing
multi-dimensional arrays optimized for numerical computation.
"""

from typing import Optional, Tuple, Union, List
import ctypes

from ._bindings import (
    get_lib, check_status, CersysError,
    CSTensorPtr, cs_float_t, cs_index_t
)
import numpy as np

__all__ = ["Tensor", "zeros", "ones", "rand_uniform", "rand_normal"]


class Tensor:
    """
    A multi-dimensional tensor for numerical computation.
    
    Tensors can be 1D or 2D and support GPU acceleration through
    automatic device placement. They integrate seamlessly with NumPy
    for data interchange.
    
    Attributes:
        shape (Tuple[int, ...]): The dimensions of the tensor.
        size (int): Total number of elements.
        ndim (int): Number of dimensions (1 or 2).
        device (str): Current device ("cpu" or "gpu").
    
    Example:
        >>> import cersys as cs
        >>> # Create from shape
        >>> t = cs.Tensor((100, 64))
        >>> print(t.shape)
        (100, 64)
        
        >>> # Create from NumPy
        >>> import numpy as np
        >>> arr = np.random.randn(100, 64).astype(np.float32)
        >>> t = cs.Tensor(arr)
        
        >>> # Convert back to NumPy
        >>> arr2 = t.numpy()
    """
    
    __slots__ = ("_ptr", "_shape", "_owns_memory", "_device")
    
    def __init__(
        self, 
        data: Union[Tuple[int, ...], "np.ndarray", List[float], None] = None,
        shape: Optional[Tuple[int, ...]] = None,
        _ptr: Optional[CSTensorPtr] = None,
        _owns_memory: bool = True,
    ):
        """
        Create a new tensor.
        
        Args:
            data: Initial data. Can be:
                - A tuple of ints: Create tensor with that shape (uninitialized)
                - A numpy array: Copy data from array
                - A list of floats: Convert to 1D tensor
                - None: Must provide _ptr for internal use
            shape: Optional shape when creating from flat data.
            _ptr: Internal use only - existing C tensor pointer.
            _owns_memory: Internal use only - whether we own the C memory.
        
        Raises:
            ValueError: If data format is invalid.
            CersysError: If tensor creation fails.
        """
        self._ptr: Optional[CSTensorPtr] = None
        self._shape: Tuple[int, ...] = ()
        self._owns_memory = _owns_memory
        self._device = "cpu"
        
        lib = get_lib()
        
        if _ptr is not None:
            # Internal: wrap existing pointer
            self._ptr = _ptr
            if shape:
                self._shape = shape
            return
        
        if data is None:
            raise ValueError("Must provide data or shape to create tensor")
        
        # Handle tuple as shape specification
        if isinstance(data, tuple) and all(isinstance(x, int) for x in data):
            if len(data) == 1:
                self._ptr = lib.cs_tensor_create_1d(cs_index_t(data[0]))
                self._shape = data
            elif len(data) == 2:
                self._ptr = lib.cs_tensor_create_2d(
                    cs_index_t(data[0]), cs_index_t(data[1])
                )
                self._shape = data
            else:
                raise ValueError("Cersys only supports 1D or 2D tensors")
            
            if not self._ptr:
                raise CersysError(-1, "Failed to create tensor")
            return
        
        # Convert to numpy array
        arr = np.asarray(data, dtype=np.float32)
        
        if arr.ndim == 0:
            arr = arr.reshape(1)
        elif arr.ndim > 2:
            raise ValueError("Cersys only supports 1D or 2D tensors")
        
        if arr.ndim == 1:
            rows, cols = arr.shape[0], 1
            self._shape = (rows,)
        else:
            rows, cols = arr.shape
            self._shape = (rows, cols)
        
        # Create tensor
        if arr.ndim == 1:
            self._ptr = lib.cs_tensor_create_1d(cs_index_t(rows))
        else:
            self._ptr = lib.cs_tensor_create_2d(
                cs_index_t(rows), cs_index_t(cols)
            )
        
        if not self._ptr:
            raise CersysError(-1, "Failed to create tensor")
        
        # Copy data
        self._copy_from_numpy(arr.flatten())
    
    def _copy_from_numpy(self, arr: np.ndarray) -> None:
        """Copy data from a flat numpy array into the tensor."""
        lib = get_lib()
        
        # Ensure contiguous float32 array
        arr = np.ascontiguousarray(arr, dtype=np.float32)
        
        # Direct memcpy for both 1D and 2D tensors (C-contiguous row-major)
        data_ptr = lib.cs_tensor_data(self._ptr)
        if not data_ptr:
            raise CersysError(-1, "Failed to access tensor data")
        ctypes.memmove(data_ptr, arr.ctypes.data, arr.nbytes)
    
    def __del__(self):
        """Release tensor memory."""
        if self._ptr and self._owns_memory:
            try:
                lib = get_lib()
                lib.cs_tensor_release(self._ptr)
            except Exception:
                pass  # Library may already be unloaded
    
    @property
    def shape(self) -> Tuple[int, ...]:
        """Get tensor shape."""
        return self._shape
    
    @property
    def ndim(self) -> int:
        """Get number of dimensions."""
        return len(self._shape)
    
    @property
    def size(self) -> int:
        """Get total number of elements."""
        result = 1
        for dim in self._shape:
            result *= dim
        return result
    
    @property
    def device(self) -> str:
        """Get current device placement."""
        return self._device
    
    @property
    def dtype(self) -> np.dtype:
        """Get data type (always float32)."""
        return np.dtype(np.float32)
    
    def __repr__(self) -> str:
        return f"Tensor(shape={self._shape}, device='{self._device}')"
    
    def __str__(self) -> str:
        return f"Tensor{self._shape}"
    
    def __len__(self) -> int:
        return self._shape[0] if self._shape else 0
    
    def __getitem__(self, idx: Union[int, Tuple[int, int]]) -> float:
        """Get element by index."""
        lib = get_lib()
        
        if isinstance(idx, tuple):
            if len(idx) != 2:
                raise IndexError("2D indexing requires exactly 2 indices")
            i, j = idx
            return float(lib.cs_tensor_get_2d(
                self._ptr, cs_index_t(i), cs_index_t(j)
            ))
        else:
            if self.ndim == 1:
                data_ptr = lib.cs_tensor_data(self._ptr)
                if not data_ptr:
                    raise CersysError(-1, "Failed to access tensor data")
                return float(data_ptr[idx])
            else:
                raise IndexError("Use 2D indexing [i, j] for 2D tensors")
    
    def __setitem__(self, idx: Union[int, Tuple[int, int]], value: float) -> None:
        """Set element by index."""
        lib = get_lib()
        
        if isinstance(idx, tuple):
            if len(idx) != 2:
                raise IndexError("2D indexing requires exactly 2 indices")
            i, j = idx
            lib.cs_tensor_set_2d(
                self._ptr, 
                cs_index_t(i), cs_index_t(j), 
                cs_float_t(float(value))
            )
        else:
            if self.ndim == 1:
                data_ptr = lib.cs_tensor_data(self._ptr)
                if not data_ptr:
                    raise CersysError(-1, "Failed to access tensor data")
                data_ptr[idx] = float(value)
            else:
                raise IndexError("Use 2D indexing [i, j] for 2D tensors")
    
    def numpy(self) -> np.ndarray:
        """
        Convert tensor to a NumPy array.
        
        Returns:
            np.ndarray: A copy of the tensor data as a float32 array.
        
        Example:
            >>> t = cs.rand_uniform((10, 5))
            >>> arr = t.numpy()
            >>> print(arr.shape, arr.dtype)
            (10, 5) float32
        """
        lib = get_lib()
        
        # Direct memcpy for both 1D and 2D tensors (C-contiguous row-major)
        data_ptr = lib.cs_tensor_data(self._ptr)
        if not data_ptr:
            raise CersysError(-1, "Failed to access tensor data")
        
        # Create view and copy (avoids double allocation)
        flat_shape = (self.size,)
        result = np.ctypeslib.as_array(data_ptr, shape=flat_shape).copy()
        return result.reshape(self._shape)
    
    def to_device(self) -> "Tensor":
        """
        Transfer tensor to GPU.
        
        Returns:
            Tensor: Self for method chaining.
        
        Raises:
            CersysError: If GPU transfer fails.
        """
        lib = get_lib()
        status = lib.cs_tensor_to_device(self._ptr)
        check_status(status)
        self._device = "gpu"
        return self
    
    def to_host(self) -> "Tensor":
        """
        Transfer tensor from GPU to CPU.
        
        Returns:
            Tensor: Self for method chaining.
        """
        lib = get_lib()
        status = lib.cs_tensor_to_host(self._ptr)
        check_status(status)
        self._device = "cpu"
        return self
    
    def clone(self) -> "Tensor":
        """
        Create a deep copy of the tensor.
        
        Returns:
            Tensor: A new tensor with copied data.
        """
        lib = get_lib()
        new_ptr = lib.cs_tensor_clone(self._ptr)
        if not new_ptr:
            raise CersysError(-1, "Failed to clone tensor")
        return Tensor(_ptr=new_ptr, shape=self._shape)
    
    def row(self, idx: int) -> np.ndarray:
        """
        Get a row as a NumPy array.
        
        Args:
            idx: Row index.
        
        Returns:
            np.ndarray: The row data as a 1D float32 array.
        """
        if self.ndim != 2:
            raise ValueError("row() only works on 2D tensors")
        
        lib = get_lib()
        cols = self._shape[1]
        result = np.zeros(cols, dtype=np.float32)
        
        for j in range(cols):
            result[j] = lib.cs_tensor_get_2d(
                self._ptr, cs_index_t(idx), cs_index_t(j)
            )
        
        return result
    
    def fill_uniform(self, low: float = 0.0, high: float = 1.0) -> "Tensor":
        """
        Fill tensor with uniform random values.
        
        Args:
            low: Lower bound (inclusive).
            high: Upper bound (exclusive).
        
        Returns:
            Tensor: Self for method chaining.
        """
        lib = get_lib()
        lib.cs_rng_fill_uniform(self._ptr, cs_float_t(low), cs_float_t(high))
        return self
    
    def save(self, path: str, name: Optional[str] = None) -> None:
        """
        Save tensor to a file in native format.
        
        Args:
            path: File path for the tensor file.
            name: Optional tensor name stored in the file metadata.
        """
        lib = get_lib()
        name_bytes = name.encode('utf-8') if name else None
        status = lib.cs_tensor_save(self._ptr, path.encode('utf-8'), name_bytes)
        check_status(status)
    
    def to_npy(self, path: str) -> None:
        """
        Export tensor to NumPy .npy format.
        
        Args:
            path: File path for the .npy file.
        """
        lib = get_lib()
        status = lib.cs_tensor_to_npy(self._ptr, path.encode('utf-8'))
        check_status(status)
    
    @classmethod
    def load(cls, path: str) -> "Tensor":
        """
        Load tensor from a native format file.
        
        Args:
            path: Path to the tensor file.
        
        Returns:
            Tensor: The loaded tensor.
        """
        lib = get_lib()
        ptr = lib.cs_tensor_load(path.encode('utf-8'))
        if not ptr:
            raise CersysError(-1, f"Failed to load tensor from {path}")
        
        # Extract shape from the loaded tensor
        ndim = lib.cs_tensor_ndim(ptr)
        shape = tuple(lib.cs_tensor_dim(ptr, i) for i in range(ndim))
        
        return cls(_ptr=ptr, shape=shape)
    
    @property
    def _c_ptr(self) -> CSTensorPtr:
        """Get the underlying C pointer (internal use)."""
        return self._ptr


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def zeros(shape: Union[int, Tuple[int, ...]], dtype: Optional[np.dtype] = None) -> Tensor:
    """
    Create a tensor filled with zeros.
    
    Args:
        shape: Tensor shape. Can be an int for 1D or tuple for 1D/2D.
        dtype: Ignored (always float32). For NumPy compatibility.
    
    Returns:
        Tensor: A zero-initialized tensor.
    
    Example:
        >>> t = cs.zeros((100, 64))
        >>> print(t[0, 0])
        0.0
    """
    lib = get_lib()
    
    if isinstance(shape, int):
        shape = (shape,)
    
    if len(shape) == 1:
        ptr = lib.cs_tensor_create_1d(cs_index_t(shape[0]))
        result_shape = shape
    elif len(shape) == 2:
        ptr = lib.cs_tensor_zeros_2d(cs_index_t(shape[0]), cs_index_t(shape[1]))
        result_shape = shape
    else:
        raise ValueError("Only 1D and 2D tensors are supported")
    
    if not ptr:
        raise CersysError(-1, "Failed to create zeros tensor")
    
    return Tensor(_ptr=ptr, shape=result_shape)


def ones(shape: Union[int, Tuple[int, ...]], dtype: Optional[np.dtype] = None) -> Tensor:
    """
    Create a tensor filled with ones.
    
    Args:
        shape: Tensor shape. Can be an int for 1D or tuple for 1D/2D.
        dtype: Ignored (always float32). For NumPy compatibility.
    
    Returns:
        Tensor: A tensor filled with ones.
    
    Example:
        >>> t = cs.ones((10, 10))
        >>> print(t[5, 5])
        1.0
    """
    # Create zeros and fill with ones
    t = zeros(shape)
    lib = get_lib()

    data_ptr = lib.cs_tensor_data(t._ptr)
    if not data_ptr:
        raise CersysError(-1, "Failed to access tensor data")

    # Fill via NumPy view for speed (works for both 1D and 2D)
    arr_view = np.ctypeslib.as_array(data_ptr, shape=(t.size,))
    arr_view.fill(1.0)

    return t


def rand_uniform(
    shape: Union[int, Tuple[int, ...]], 
    low: float = 0.0, 
    high: float = 1.0
) -> Tensor:
    """
    Create a tensor with uniform random values.
    
    Args:
        shape: Tensor shape.
        low: Lower bound (inclusive).
        high: Upper bound (exclusive).
    
    Returns:
        Tensor: A tensor with random values uniformly distributed in [low, high).
    
    Example:
        >>> t = cs.rand_uniform((1000, 64), -0.1, 0.1)
        >>> arr = t.numpy()
        >>> print(arr.min(), arr.max())  # Should be in [-0.1, 0.1)
    """
    if isinstance(shape, int):
        shape = (shape,)
    
    t = Tensor(shape)
    t.fill_uniform(low, high)
    return t


def rand_normal(
    shape: Union[int, Tuple[int, ...]], 
    mean: float = 0.0, 
    std: float = 1.0
) -> Tensor:
    """
    Create a tensor with normally distributed random values.
    
    Args:
        shape: Tensor shape.
        mean: Mean of the distribution.
        std: Standard deviation.
    
    Returns:
        Tensor: A tensor with random values from N(mean, std^2).
    
    Example:
        >>> t = cs.rand_normal((1000, 64), mean=0.0, std=0.02)
    """
    if isinstance(shape, int):
        shape = (shape,)
    
    # Generate using NumPy and copy
    arr = np.random.normal(mean, std, shape).astype(np.float32)
    return Tensor(arr)


# NumPy array protocol support
def _array_ufunc_not_implemented(*args, **kwargs):
    return NotImplemented


Tensor.__array_ufunc__ = _array_ufunc_not_implemented


def __array__(self, dtype=None):
    """NumPy array interface."""
    arr = self.numpy()
    if dtype is not None:
        arr = arr.astype(dtype)
    return arr


Tensor.__array__ = __array__
