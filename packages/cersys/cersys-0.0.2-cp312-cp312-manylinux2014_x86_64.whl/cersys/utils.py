"""
Utility functions.

General-purpose utilities for working with Cersys.
"""

import numpy as np
from typing import Optional, Sequence

from ._bindings import get_lib

__all__ = ["set_seed", "sample_negatives"]


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility.
    
    This affects both the C library's RNG and NumPy's RNG.
    
    Args:
        seed: Random seed (non-negative integer).
    
    Example:
        >>> cs.set_seed(42)
        >>> # Now all random operations are reproducible
    """
    import ctypes
    lib = get_lib()
    lib.cs_rng_seed(ctypes.c_uint64(seed))
    np.random.seed(seed)


def sample_negatives(
    n_samples: int,
    num_items: int,
    exclude: Optional[Sequence[int]] = None,
) -> np.ndarray:
    """
    Sample negative item IDs uniformly.
    
    Args:
        n_samples: Number of negative samples to generate.
        num_items: Total number of items (samples from [0, num_items)).
        exclude: Optional set of item IDs to exclude from sampling.
    
    Returns:
        np.ndarray: Array of sampled negative item IDs (uint32).
    
    Example:
        >>> negatives = cs.sample_negatives(1000, num_items=50000)
        >>> print(negatives.shape)
        (1000,)
    """
    if exclude is not None:
        # Use NumPy for exclusion logic
        exclude_set = set(exclude)
        candidates = [i for i in range(num_items) if i not in exclude_set]
        if len(candidates) == 0:
            raise ValueError("No valid items to sample from after exclusions")
        return np.random.choice(candidates, size=n_samples).astype(np.uint32)
    
    # Use NumPy's fast sampling
    return np.random.randint(0, num_items, size=n_samples, dtype=np.uint32)


def compute_metrics(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    k: int = 10,
) -> dict:
    """
    Compute common recommendation metrics.
    
    Args:
        predictions: Predicted rankings (array of item IDs per user).
        ground_truth: Ground truth positive items per user.
        k: Cutoff for metrics@k.
    
    Returns:
        dict: Dictionary with metrics:
            - precision@k
            - recall@k
            - ndcg@k
            - hit_rate@k
    
    Example:
        >>> # predictions[i] = top-k items for user i
        >>> # ground_truth[i] = set of relevant items for user i
        >>> metrics = cs.compute_metrics(predictions, ground_truth, k=10)
        >>> print(f"NDCG@10: {metrics['ndcg@k']:.4f}")
    """
    n_users = len(predictions)
    
    precision_sum = 0.0
    recall_sum = 0.0
    ndcg_sum = 0.0
    hits = 0
    
    for i in range(n_users):
        pred = predictions[i][:k] if len(predictions[i]) >= k else predictions[i]
        true_set = set(ground_truth[i]) if hasattr(ground_truth[i], '__iter__') else {ground_truth[i]}
        
        # Precision@k
        hits_in_k = len(set(pred) & true_set)
        precision_sum += hits_in_k / k
        
        # Recall@k
        if len(true_set) > 0:
            recall_sum += hits_in_k / len(true_set)
        
        # Hit rate
        if hits_in_k > 0:
            hits += 1
        
        # NDCG@k
        dcg = 0.0
        for j, item in enumerate(pred):
            if item in true_set:
                dcg += 1.0 / np.log2(j + 2)
        
        # Ideal DCG
        idcg = sum(1.0 / np.log2(j + 2) for j in range(min(len(true_set), k)))
        if idcg > 0:
            ndcg_sum += dcg / idcg
    
    return {
        f"precision@{k}": precision_sum / n_users,
        f"recall@{k}": recall_sum / n_users,
        f"ndcg@{k}": ndcg_sum / n_users,
        f"hit_rate@{k}": hits / n_users,
    }
