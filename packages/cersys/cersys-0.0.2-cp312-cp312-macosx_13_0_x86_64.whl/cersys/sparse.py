"""
Sparse matrix support.

Sparse matrices are essential for representing user-item interaction
data efficiently.
"""

from typing import Optional, Tuple
import ctypes
import numpy as np

from ._bindings import (
    get_lib, check_status, CersysError,
    CSSparseMatrixPtr, cs_index_t, cs_float_t,
)
from .tensor import Tensor

__all__ = ["SparseMatrix"]


class SparseMatrix:
    """
    Compressed Sparse Row (CSR) matrix.
    
    Efficient representation for sparse data like user-item interactions.
    Supports GPU transfer and conversion to dense format.
    
    Attributes:
        shape (Tuple[int, int]): Matrix dimensions (rows, cols).
        nnz (int): Number of non-zero elements.
    
    Example:
        >>> # Create from scipy sparse matrix
        >>> from scipy import sparse
        >>> scipy_csr = sparse.random(1000, 5000, density=0.01, format='csr')
        >>> cs_sparse = cs.SparseMatrix.from_scipy(scipy_csr)
        
        >>> # Access elements
        >>> value = cs_sparse[42, 100]
        
        >>> # Convert to dense
        >>> dense = cs_sparse.to_dense()
    """
    
    __slots__ = ("_ptr", "_shape", "_nnz")
    
    def __init__(
        self,
        rows: int,
        cols: int,
        nnz: int,
        _ptr: Optional[CSSparseMatrixPtr] = None,
    ):
        """
        Create a sparse matrix.
        
        Args:
            rows: Number of rows.
            cols: Number of columns.
            nnz: Maximum number of non-zero elements.
            _ptr: Internal use - existing C pointer.
        """
        self._shape = (rows, cols)
        self._nnz = nnz
        
        if _ptr is not None:
            self._ptr = _ptr
        else:
            lib = get_lib()
            self._ptr = lib.cs_sparse_create(
                cs_index_t(rows),
                cs_index_t(cols),
                cs_index_t(nnz),  # Use cs_index_t to match C signature
            )
            if not self._ptr:
                raise CersysError(-1, "Failed to create sparse matrix")
    
    def __del__(self):
        if self._ptr:
            try:
                lib = get_lib()
                lib.cs_sparse_release(self._ptr)
            except Exception:
                pass
    
    @property
    def shape(self) -> Tuple[int, int]:
        """Get matrix shape."""
        return self._shape
    
    @property
    def nnz(self) -> int:
        """Get number of non-zero elements."""
        return self._nnz
    
    def __getitem__(self, idx: Tuple[int, int]) -> float:
        """Get element by index."""
        if not isinstance(idx, tuple) or len(idx) != 2:
            raise IndexError("Sparse matrix requires 2D indexing [i, j]")
        
        lib = get_lib()
        return float(lib.cs_sparse_get(
            self._ptr,
            cs_index_t(idx[0]),
            cs_index_t(idx[1]),
        ))
    
    def __repr__(self) -> str:
        return f"SparseMatrix(shape={self._shape}, nnz={self._nnz})"
    
    def to_dense(self) -> Tensor:
        """
        Convert to a dense Tensor.
        
        Returns:
            Tensor: Dense tensor with the same data.
        
        Warning:
            This can consume significant memory for large sparse matrices.
        """
        lib = get_lib()
        tensor_ptr = lib.cs_sparse_to_dense(self._ptr)
        if not tensor_ptr:
            raise CersysError(-1, "Failed to convert sparse to dense")
        return Tensor(_ptr=tensor_ptr, shape=self._shape)
    
    def to_device(self) -> "SparseMatrix":
        """
        Transfer sparse matrix to GPU.
        
        Returns:
            SparseMatrix: Self for method chaining.
        """
        lib = get_lib()
        status = lib.cs_sparse_to_device(self._ptr)
        check_status(status)
        return self
    
    @classmethod
    def from_scipy(cls, scipy_csr) -> "SparseMatrix":
        """
        Create from a scipy CSR sparse matrix.
        
        Args:
            scipy_csr: A scipy.sparse.csr_matrix.
        
        Returns:
            SparseMatrix: A new sparse matrix with copied data.
        
        Example:
            >>> from scipy import sparse
            >>> sp = sparse.random(100, 100, density=0.1, format='csr')
            >>> cs_sp = cs.SparseMatrix.from_scipy(sp)
        """
        try:
            from scipy import sparse
        except ImportError:
            raise ImportError("scipy is required for from_scipy()")
        
        if not sparse.isspmatrix_csr(scipy_csr):
            scipy_csr = scipy_csr.tocsr()
        
        rows, cols = scipy_csr.shape
        nnz = scipy_csr.nnz
        
        # Create the sparse matrix
        lib = get_lib()
        ptr = lib.cs_sparse_create(
            cs_index_t(rows),
            cs_index_t(cols),
            cs_index_t(nnz),
        )
        if not ptr:
            raise CersysError(-1, "Failed to create sparse matrix")
        
        # Get pointers to internal C arrays
        row_ptr_c = lib.cs_sparse_row_ptr(ptr)
        col_idx_c = lib.cs_sparse_col_idx(ptr)
        values_c = lib.cs_sparse_values(ptr)
        
        # Convert scipy arrays to contiguous numpy arrays with correct dtype
        row_ptr_np = np.ascontiguousarray(scipy_csr.indptr, dtype=np.uint32)
        col_idx_np = np.ascontiguousarray(scipy_csr.indices, dtype=np.uint32)
        values_np = np.ascontiguousarray(scipy_csr.data, dtype=np.float32)
        
        # Copy data using memmove
        ctypes.memmove(row_ptr_c, row_ptr_np.ctypes.data, row_ptr_np.nbytes)
        ctypes.memmove(col_idx_c, col_idx_np.ctypes.data, col_idx_np.nbytes)
        ctypes.memmove(values_c, values_np.ctypes.data, values_np.nbytes)
        
        # Create wrapper object
        obj = cls.__new__(cls)
        obj._ptr = ptr
        obj._shape = (rows, cols)
        obj._nnz = nnz
        return obj
    
    @classmethod
    def from_coo(
        cls,
        rows: np.ndarray,
        cols: np.ndarray,
        values: np.ndarray,
        shape: Tuple[int, int],
    ) -> "SparseMatrix":
        """
        Create from COO (coordinate) format arrays.
        
        Args:
            rows: Row indices.
            cols: Column indices.
            values: Non-zero values.
            shape: Matrix shape (n_rows, n_cols).
        
        Returns:
            SparseMatrix: A new sparse matrix.
        
        Example:
            >>> rows = np.array([0, 1, 2])
            >>> cols = np.array([1, 0, 2])
            >>> vals = np.array([1.0, 2.0, 3.0])
            >>> sp = cs.SparseMatrix.from_coo(rows, cols, vals, (3, 3))
        """
        try:
            from scipy import sparse
        except ImportError:
            raise ImportError("scipy is required for from_coo()")
        
        # Convert to scipy COO then to CSR
        coo = sparse.coo_matrix((values, (rows, cols)), shape=shape)
        csr = coo.tocsr()
        
        # Delegate to from_scipy
        return cls.from_scipy(csr)
    
    def row_nnz(self, row: int) -> int:
        """
        Get the number of non-zeros in a row.
        
        Args:
            row: Row index.
        
        Returns:
            int: Number of non-zero elements in the row.
        """
        lib = get_lib()
        return int(lib.cs_sparse_row_nnz(self._ptr, cs_index_t(row)))
    
    def get_row(
        self, 
        row: int, 
        max_nnz: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get non-zero entries in a row.
        
        Args:
            row: Row index.
            max_nnz: Maximum entries to return.
        
        Returns:
            Tuple of (column_indices, values) arrays.
        """
        lib = get_lib()
        
        # Allocate output buffers
        cols_buf = (cs_index_t * max_nnz)()
        vals_buf = (cs_float_t * max_nnz)()
        out_count = cs_index_t(0)
        
        status = lib.cs_sparse_get_row(
            self._ptr,
            cs_index_t(row),
            cols_buf,
            vals_buf,
            ctypes.byref(out_count),
        )
        check_status(status)
        
        # Use the actual count returned by the C function
        actual_nnz = min(int(out_count.value), max_nnz)
        
        return (
            np.array(cols_buf[:actual_nnz], dtype=np.uint32),
            np.array(vals_buf[:actual_nnz], dtype=np.float32),
        )
