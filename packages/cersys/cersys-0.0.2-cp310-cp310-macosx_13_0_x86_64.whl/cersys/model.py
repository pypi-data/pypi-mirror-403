"""
Recommender system models.

This module provides high-level model classes for building
recommender systems with Cersys.
"""

from typing import Optional, List, Tuple, Union, Dict, Sequence
from abc import ABC, abstractmethod
import numpy as np
import json
import tempfile
import os

from ._bindings import (
    get_lib, check_status, CersysError,
    CSModelPtr, cs_id_t, cs_index_t, cs_float_t,
    POINTER, ctypes,
    CS_ACTIVATION_RELU, CS_ACTIVATION_SIGMOID, CS_ACTIVATION_TANH,
    CS_ACTIVATION_LEAKY_RELU, CS_ACTIVATION_GELU, CS_ACTIVATION_SOFTMAX,
    CS_MODEL_MATRIX_FACTORIZATION,
)

__all__ = ["Model", "MatrixFactorization"]


# Activation name to constant mapping
ACTIVATION_MAP = {
    "relu": CS_ACTIVATION_RELU,
    "sigmoid": CS_ACTIVATION_SIGMOID,
    "tanh": CS_ACTIVATION_TANH,
    "leaky_relu": CS_ACTIVATION_LEAKY_RELU,
    "gelu": CS_ACTIVATION_GELU,
    "softmax": CS_ACTIVATION_SOFTMAX,
}


class Model(ABC):
    """
    Abstract base class for all Cersys models.
    
    Models encapsulate the parameters and architecture of a recommender
    system. They support both training and inference modes.
    """
    
    __slots__ = ("_ptr", "_training")
    
    def __init__(self):
        self._ptr: Optional[CSModelPtr] = None
        self._training = True
    
    def __del__(self):
        if self._ptr:
            try:
                lib = get_lib()
                lib.cs_model_release(self._ptr)
            except Exception:
                pass
    
    @property
    def training(self) -> bool:
        """Whether the model is in training mode."""
        return self._training
    
    def train(self) -> "Model":
        """
        Set the model to training mode.
        
        In training mode, stochastic layers like Dropout are active.
        
        Returns:
            Model: Self for method chaining.
        """
        lib = get_lib()
        lib.cs_model_train(self._ptr)
        self._training = True
        return self
    
    def eval(self) -> "Model":
        """
        Set the model to evaluation mode.
        
        In evaluation mode, stochastic layers like Dropout are disabled.
        
        Returns:
            Model: Self for method chaining.
        """
        lib = get_lib()
        lib.cs_model_eval(self._ptr)
        self._training = False
        return self
    
    @property
    def num_parameters(self) -> int:
        """Get the total number of trainable parameters."""
        lib = get_lib()
        return int(lib.cs_model_num_parameters(self._ptr))
    
    @abstractmethod
    def forward_user(self, user_ids: Union[int, np.ndarray]) -> np.ndarray:
        """Compute user embeddings."""
        pass
    
    @abstractmethod
    def forward_item(self, item_ids: Union[int, np.ndarray]) -> np.ndarray:
        """Compute item embeddings."""
        pass
    
    @abstractmethod
    def score(
        self, 
        user_id: int, 
        item_ids: Union[int, Sequence[int], np.ndarray]
    ) -> np.ndarray:
        """Score user-item pairs."""
        pass
    
    @abstractmethod
    def recommend(
        self, 
        user_id: int, 
        top_k: int = 10,
        exclude_items: Optional[Sequence[int]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get top-k item recommendations for a user.
        
        Args:
            user_id: The user to generate recommendations for.
            top_k: Number of items to recommend.
            exclude_items: Items to exclude (e.g., already interacted items).
        
        Returns:
            Tuple of (item_ids, scores) arrays.
        
        Note:
            This is a convenience method that scores all items. For large
            item catalogs, consider using approximate nearest neighbor search.
        """
        pass
    
    def save(self, path: str) -> None:
        """
        Save model to a file.
        
        Args:
            path: File path. Will be saved in native .csm format.
        """
        lib = get_lib()
        status = lib.cs_model_save(self._ptr, path.encode('utf-8'))
        check_status(status)
    
    @classmethod
    def load(cls, path: str) -> "Model":
        """
        Load a model from file.
        
        Args:
            path: Path to the model file.
        
        Returns:
            Model: The loaded model.
        
        Note:
            The returned model type depends on what was saved.
        """
        lib = get_lib()
        ptr = lib.cs_model_load(path.encode('utf-8'))
        if not ptr:
            raise CersysError(-1, f"Failed to load model from {path}")

        # Read metadata to determine concrete model type
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            status = lib.cs_model_metadata_json(ptr, tmp_path.encode('utf-8'))
            check_status(status)
            with open(tmp_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        model_type = meta.get("model_type")
        num_users = int(meta.get("num_users", 0))
        num_items = int(meta.get("num_items", 0))
        embedding_dim = int(meta.get("embedding_dim", 0))

        if model_type == CS_MODEL_MATRIX_FACTORIZATION:
            model = object.__new__(MatrixFactorization)
            model._ptr = ptr
            model._training = False
            model.num_users = num_users
            model.num_items = num_items
            model.embedding_dim = embedding_dim
            model.use_biases = True
            return model

        # Fallback to base class if unknown
        model = object.__new__(cls)
        model._ptr = ptr
        model._training = False
        return model
    
    def to_safetensors(self, path: str) -> None:
        """
        Export model weights to HuggingFace safetensors format.
        
        Args:
            path: Output file path.
        """
        lib = get_lib()
        status = lib.cs_model_to_safetensors(self._ptr, path.encode('utf-8'))
        check_status(status)
    
    def metadata_json(self) -> str:
        """
        Get model metadata as JSON string.
        
        Returns:
            str: JSON string with model configuration and statistics.
        """
        lib = get_lib()
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            status = lib.cs_model_metadata_json(self._ptr, tmp_path.encode('utf-8'))
            check_status(status)
            with open(tmp_path, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    @property
    def _c_ptr(self) -> CSModelPtr:
        """Get the underlying C pointer (internal use)."""
        return self._ptr


class MatrixFactorization(Model):
    """
    Matrix Factorization model for collaborative filtering.
    
    This implements the classic matrix factorization approach where
    users and items are represented as low-dimensional embedding vectors.
    The predicted score is the dot product of embeddings (optionally
    with bias terms).
    
    Attributes:
        num_users (int): Number of users.
        num_items (int): Number of items.
        embedding_dim (int): Dimension of embeddings.
        use_biases (bool): Whether bias terms are used.
    
    Example:
        >>> model = cs.MatrixFactorization(
        ...     num_users=10000,
        ...     num_items=50000,
        ...     embedding_dim=64,
        ...     use_biases=True
        ... )
        >>> scores = model.score(user_id=42, item_ids=[1, 2, 3, 4, 5])
        >>> print(scores)
        [0.23, -0.15, 0.87, 0.02, -0.34]
    """
    
    __slots__ = ("num_users", "num_items", "embedding_dim", "use_biases")
    
    def __init__(
        self,
        num_users: int,
        num_items: int,
        embedding_dim: int = 64,
        use_biases: bool = True,
    ):
        """
        Create a new Matrix Factorization model.
        
        Args:
            num_users: Number of users in the system.
            num_items: Number of items in the catalog.
            embedding_dim: Dimension of user and item embeddings.
            use_biases: Whether to include bias terms for users and items.
        """
        super().__init__()
        
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        self.use_biases = use_biases
        
        lib = get_lib()
        self._ptr = lib.cs_model_mf_create(
            cs_id_t(num_users),
            cs_id_t(num_items),
            cs_index_t(embedding_dim),
            use_biases,
        )
        
        if not self._ptr:
            raise CersysError(-1, "Failed to create MF model")
    
    def forward_user(self, user_ids: Union[int, np.ndarray]) -> np.ndarray:
        """
        Get user embeddings.
        
        Args:
            user_ids: A single user ID or array of user IDs.
        
        Returns:
            np.ndarray: User embeddings of shape (n_users, embedding_dim)
                       or (embedding_dim,) for a single user.
        """
        lib = get_lib()
        single = isinstance(user_ids, (int, np.integer))
        
        if single:
            user_ids = np.array([user_ids], dtype=np.uint32)
        else:
            user_ids = np.asarray(user_ids, dtype=np.uint32)
        
        user_arr = user_ids.ctypes.data_as(POINTER(cs_id_t))
        out_ptr = lib.cs_model_forward_user(self._ptr, user_arr, cs_index_t(len(user_ids)))
        if not out_ptr:
            raise CersysError(-1, "Failed to compute user embeddings")
        
        from .tensor import Tensor
        tensor = Tensor(_ptr=out_ptr, shape=(len(user_ids), self.embedding_dim), _owns_memory=False)
        result = tensor.numpy()
        lib.cs_tensor_release(out_ptr)
        
        return result[0] if single else result
    
    def forward_item(self, item_ids: Union[int, np.ndarray]) -> np.ndarray:
        """
        Get item embeddings.
        
        Args:
            item_ids: A single item ID or array of item IDs.
        
        Returns:
            np.ndarray: Item embeddings of shape (n_items, embedding_dim)
                       or (embedding_dim,) for a single item.
        """
        lib = get_lib()
        single = isinstance(item_ids, (int, np.integer))
        
        if single:
            item_ids = np.array([item_ids], dtype=np.uint32)
        else:
            item_ids = np.asarray(item_ids, dtype=np.uint32)
        
        item_arr = item_ids.ctypes.data_as(POINTER(cs_id_t))
        out_ptr = lib.cs_model_forward_item(self._ptr, item_arr, cs_index_t(len(item_ids)))
        if not out_ptr:
            raise CersysError(-1, "Failed to compute item embeddings")
        
        from .tensor import Tensor
        tensor = Tensor(_ptr=out_ptr, shape=(len(item_ids), self.embedding_dim), _owns_memory=False)
        result = tensor.numpy()
        lib.cs_tensor_release(out_ptr)
        
        return result[0] if single else result
    
    def score(
        self,
        user_id: Union[int, Sequence[int], np.ndarray],
        item_ids: Union[int, Sequence[int], np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Score user-item pairs using fast BLAS operations.
        
        Uses cs_model_score_items for optimized batch scoring with
        BLAS sgemv (contiguous items) or sdot (sparse items).
        
        Args:
            user_id: A single user ID or array of user IDs.
            item_ids: A single item ID or array of item IDs.
                     If user_id is scalar, scores user against all item_ids.
                     If both are arrays, they must have the same length
                     and pairs are scored element-wise.
        
        Returns:
            float: If both inputs are scalars.
            np.ndarray: Array of predicted scores.
        """
        lib = get_lib()
        
        # Determine if inputs are scalars
        user_is_scalar = isinstance(user_id, (int, np.integer))
        item_is_scalar = isinstance(item_ids, (int, np.integer))
        
        # Convert to numpy arrays
        if user_is_scalar:
            user_ids_arr = np.array([int(user_id)], dtype=np.uint32)
        else:
            user_ids_arr = np.ascontiguousarray(user_id, dtype=np.uint32)
        
        if item_is_scalar:
            item_ids_arr = np.array([int(item_ids)], dtype=np.uint32)
        else:
            item_ids_arr = np.ascontiguousarray(item_ids, dtype=np.uint32)
        
        n_users = len(user_ids_arr)
        n_items = len(item_ids_arr)
        
        # Single user, multiple items - use fast path
        if n_users == 1:
            item_arr = item_ids_arr.ctypes.data_as(POINTER(cs_id_t))
            out_scores = (cs_float_t * n_items)()
            
            status = lib.cs_model_score_items(
                self._ptr,
                cs_id_t(user_ids_arr[0]),
                item_arr,
                cs_index_t(n_items),
                out_scores,
            )
            check_status(status)
            
            scores = np.array(out_scores, dtype=np.float32)
            return float(scores[0]) if (user_is_scalar and item_is_scalar) else scores
        
        # Multiple users - need pairwise scoring
        if n_users != n_items:
            raise ValueError(
                f"When scoring multiple users, user_ids and item_ids must have "
                f"the same length. Got {n_users} users and {n_items} items."
            )
        
        # Use the batched score C function
        user_arr = user_ids_arr.ctypes.data_as(POINTER(cs_id_t))
        item_arr = item_ids_arr.ctypes.data_as(POINTER(cs_id_t))
        
        out_ptr = lib.cs_model_score(self._ptr, user_arr, item_arr, cs_index_t(n_users))
        if not out_ptr:
            raise CersysError(-1, "Failed to compute scores")
        
        from .tensor import Tensor
        tensor = Tensor(_ptr=out_ptr, shape=(n_users,), _owns_memory=False)
        scores = tensor.numpy().copy()
        lib.cs_tensor_release(out_ptr)
        
        return scores
    
    def recommend(
        self,
        user_id: int,
        top_k: int = 10,
        exclude_items: Optional[Sequence[int]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get top-k item recommendations for a user.
        
        Uses optimized BLAS sgemv for fast matrix-vector multiplication
        and heap-based top-k selection.
        
        Args:
            user_id: The user to generate recommendations for.
            top_k: Number of items to recommend.
            exclude_items: Items to exclude (e.g., already interacted items).
        
        Returns:
            Tuple of (item_ids, scores) arrays sorted by score descending.
        """
        lib = get_lib()
        
        # Fast path: use C implementation when no exclusions
        if exclude_items is None or len(exclude_items) == 0:
            out_items = (cs_id_t * top_k)()
            out_scores = (cs_float_t * top_k)()
            
            status = lib.cs_recommend(
                self._ptr,
                cs_id_t(user_id),
                cs_index_t(top_k),
                out_items,
                out_scores
            )
            check_status(status)
            
            item_ids = np.array(out_items, dtype=np.uint32)
            scores = np.array(out_scores, dtype=np.float32)
            return item_ids, scores
        
        # Slow path with exclusions: score all items in Python
        all_items = np.arange(self.num_items, dtype=np.uint32)
        scores = self.score(user_id, all_items)
        
        # Exclude items
        exclude_set = set(exclude_items)
        mask = np.array([i not in exclude_set for i in range(self.num_items)])
        scores = np.where(mask, scores, -np.inf)
        
        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        top_scores = scores[top_indices]
        
        return top_indices.astype(np.uint32), top_scores
    
    def train_step_bpr(
        self,
        user_ids: np.ndarray,
        pos_item_ids: np.ndarray,
        neg_item_ids: np.ndarray,
        learning_rate: float = 0.01,
        regularization: float = 0.001,
        lr: Optional[float] = None,
        reg: Optional[float] = None,
    ) -> None:
        """
        Perform one BPR (Bayesian Personalized Ranking) training step.
        
        Args:
            user_ids: Array of user IDs.
            pos_item_ids: Array of positive (interacted) item IDs.
            neg_item_ids: Array of negative (sampled) item IDs.
            learning_rate: SGD learning rate.
            regularization: L2 regularization strength.
        """
        if lr is not None:
            learning_rate = lr
        if reg is not None:
            regularization = reg

        lib = get_lib()
        
        # Ensure contiguous arrays with correct dtype
        user_ids = np.ascontiguousarray(user_ids, dtype=np.uint32)
        pos_item_ids = np.ascontiguousarray(pos_item_ids, dtype=np.uint32)
        neg_item_ids = np.ascontiguousarray(neg_item_ids, dtype=np.uint32)
        
        batch_size = len(user_ids)
        assert len(pos_item_ids) == batch_size
        assert len(neg_item_ids) == batch_size
        
        # Use zero-copy pointer access instead of element-by-element unpacking
        user_arr = user_ids.ctypes.data_as(POINTER(cs_id_t))
        pos_arr = pos_item_ids.ctypes.data_as(POINTER(cs_id_t))
        neg_arr = neg_item_ids.ctypes.data_as(POINTER(cs_id_t))
        
        status = lib.cs_model_train_step_bpr(
            self._ptr,
            user_arr,
            pos_arr,
            neg_arr,
            cs_index_t(batch_size),
            cs_float_t(learning_rate),
            cs_float_t(regularization),
        )
        check_status(status)
    
    def fit(
        self,
        user_ids: np.ndarray,
        item_ids: np.ndarray,
        ratings: Optional[np.ndarray] = None,
        epochs: int = 10,
        batch_size: int = 256,
        learning_rate: float = 0.01,
        regularization: float = 0.001,
        num_negatives: int = 1,
        verbose: bool = True,
    ) -> Dict[str, List[float]]:
        """
        Train the model on user-item interactions.
        
        Args:
            user_ids: Array of user IDs for interactions.
            item_ids: Array of item IDs for interactions.
            ratings: Optional ratings (unused for BPR, kept for API compat).
            epochs: Number of training epochs.
            batch_size: Mini-batch size.
            learning_rate: SGD learning rate.
            regularization: L2 regularization strength.
            num_negatives: Number of negative samples per positive.
            verbose: Whether to print training progress.
        
        Returns:
            dict: Training history with metrics per epoch.
        
        Example:
            >>> history = model.fit(
            ...     user_ids=train_users,
            ...     item_ids=train_items,
            ...     epochs=20,
            ...     batch_size=512,
            ...     learning_rate=0.01,
            ... )
        """
        lib = get_lib()

        user_ids = np.asarray(user_ids, dtype=np.uint32)
        item_ids = np.asarray(item_ids, dtype=np.uint32)
        n_interactions = len(user_ids)

        # Pre-allocate reusable batch buffers
        batch_users_buf = np.empty(batch_size, dtype=np.uint32)
        batch_pos_buf = np.empty(batch_size, dtype=np.uint32)
        batch_neg_buf = np.empty(batch_size, dtype=np.uint32)
        
        history = {"epoch": [], "loss": []}
        
        for epoch in range(epochs):
            # Shuffle data
            perm = np.random.permutation(n_interactions)
            user_ids_shuffled = user_ids[perm]
            item_ids_shuffled = item_ids[perm]
            
            epoch_loss = 0.0
            n_batches = 0
            
            for start in range(0, n_interactions, batch_size):
                end = min(start + batch_size, n_interactions)
                curr_batch = end - start

                # Fill reusable buffers
                batch_users = batch_users_buf[:curr_batch]
                batch_pos = batch_pos_buf[:curr_batch]
                batch_neg = batch_neg_buf[:curr_batch]

                np.copyto(batch_users, user_ids_shuffled[start:end])
                np.copyto(batch_pos, item_ids_shuffled[start:end])

                # Sample negatives in C (fast path)
                user_ptr = batch_users.ctypes.data_as(POINTER(cs_id_t))
                neg_ptr = batch_neg.ctypes.data_as(POINTER(cs_id_t))
                lib.cs_sample_negatives_uniform(
                    None,
                    user_ptr,
                    neg_ptr,
                    cs_index_t(curr_batch),
                    cs_index_t(self.num_items),
                )

                # Training step
                self.train_step_bpr(
                    batch_users,
                    batch_pos,
                    batch_neg,
                    learning_rate,
                    regularization,
                )
                
                n_batches += 1
            
            history["epoch"].append(epoch + 1)
            history["loss"].append(epoch_loss / max(n_batches, 1))
            
            if verbose:
                print(f"Epoch {epoch + 1}/{epochs}")
        
        return history
    
    def fit_als(
        self,
        user_ids: np.ndarray,
        item_ids: np.ndarray,
        ratings: Optional[np.ndarray] = None,
        epochs: int = 15,
        alpha: float = 40.0,
        regularization: float = 0.01,
        num_threads: int = 0,
        verbose: bool = True,
    ) -> Dict[str, List[float]]:
        """
        Train the model using ALS (Alternating Least Squares).
        
        ALS is typically faster than BPR for matrix factorization and
        often achieves comparable or better results on implicit feedback
        data. It alternates between fixing item factors and solving for
        users, then fixing user factors and solving for items.
        
        Args:
            user_ids: Array of user IDs for interactions.
            item_ids: Array of item IDs for interactions.
            ratings: Optional confidence weights (default: all 1s).
            epochs: Number of ALS iterations.
            alpha: Confidence scaling factor (c_ui = 1 + alpha * r_ui).
                   Higher values give more weight to observed interactions.
            regularization: L2 regularization strength (lambda).
            num_threads: Number of threads (0 = auto-detect).
            verbose: Whether to print training progress.
        
        Returns:
            dict: Training history.
        
        Example:
            >>> history = model.fit_als(
            ...     user_ids=train_users,
            ...     item_ids=train_items,
            ...     epochs=15,
            ...     alpha=40.0,
            ...     regularization=0.01,
            ... )
        """
        from scipy import sparse
        import time
        
        lib = get_lib()
        
        user_ids = np.asarray(user_ids, dtype=np.uint32)
        item_ids = np.asarray(item_ids, dtype=np.uint32)
        
        if ratings is None:
            ratings = np.ones(len(user_ids), dtype=np.float32)
        else:
            ratings = np.asarray(ratings, dtype=np.float32)
        
        # Build scipy CSR sparse matrix
        csr_matrix = sparse.csr_matrix(
            (ratings, (user_ids, item_ids)),
            shape=(self.num_users, self.num_items),
            dtype=np.float32
        )
        
        # Create C sparse matrix from scipy CSR
        nnz = csr_matrix.nnz
        if nnz > np.iinfo(np.uint32).max:
            raise CersysError(-1, "Sparse matrix too large for cs_index_t")
        sparse_ptr = lib.cs_sparse_create(
            cs_index_t(self.num_users),
            cs_index_t(self.num_items),
            cs_index_t(nnz)
        )
        
        if not sparse_ptr:
            raise CersysError(-1, "Failed to create sparse matrix")
        
        # Get pointers to sparse matrix data
        # Access internal CSR arrays and copy data
        row_ptr = lib.cs_sparse_row_ptr(sparse_ptr)
        col_idx = lib.cs_sparse_col_idx(sparse_ptr)
        values = lib.cs_sparse_values(sparse_ptr)
        
        # Convert scipy arrays to contiguous numpy arrays with correct dtype
        # then use direct memcpy (zero-copy pointer access)
        row_ptr_np = np.ascontiguousarray(csr_matrix.indptr, dtype=np.uint32)
        col_idx_np = np.ascontiguousarray(csr_matrix.indices, dtype=np.uint32)
        values_np = np.ascontiguousarray(csr_matrix.data, dtype=np.float32)
        
        ctypes.memmove(row_ptr, row_ptr_np.ctypes.data, row_ptr_np.nbytes)
        ctypes.memmove(col_idx, col_idx_np.ctypes.data, col_idx_np.nbytes)
        ctypes.memmove(values, values_np.ctypes.data, values_np.nbytes)
        
        history = {"epoch": [], "time": []}
        
        for epoch in range(epochs):
            start_time = time.time()
            
            status = lib.cs_model_train_als_epoch(
                self._ptr,
                sparse_ptr,
                cs_float_t(alpha),
                cs_float_t(regularization),
                cs_index_t(num_threads)
            )
            check_status(status)
            
            elapsed = time.time() - start_time
            history["epoch"].append(epoch + 1)
            history["time"].append(elapsed)
            
            if verbose:
                print(f"Epoch {epoch + 1}/{epochs} ({elapsed:.3f}s)")
        
        lib.cs_sparse_release(sparse_ptr)
        
        return history
    
    def __repr__(self) -> str:
        return (
            f"MatrixFactorization(num_users={self.num_users}, "
            f"num_items={self.num_items}, embedding_dim={self.embedding_dim}, "
            f"use_biases={self.use_biases})"
        )

