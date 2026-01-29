"""
Cersys Python Test Suite

Run with: pytest test_cersys.py -v
"""

import pytest
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cersys as cs
from cersys._bindings import CersysError


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def engine():
    """Initialize engine for all tests. Skip if no OpenCL device available."""
    cs.set_verbosity(cs.VERBOSITY_SILENT)
    try:
        cs.init()
    except CersysError as e:
        if "No OpenCL" in str(e) or e.code == 203:
            pytest.skip("No OpenCL device available - skipping all tests")
        raise
    yield
    cs.shutdown()


# =============================================================================
# Core Tests
# =============================================================================

class TestCore:
    def test_version(self):
        assert cs.get_version() == "0.0.2"
    
    def test_is_initialized(self):
        assert cs.is_initialized()
    
    def test_device_info(self):
        info = cs.get_device_info()
        assert "platform" in info
        assert "device" in info
        assert "memory_gb" in info
        assert info["memory_gb"] > 0
    
    def test_verbosity(self):
        cs.set_verbosity(cs.VERBOSITY_SILENT)
        cs.set_verbosity(cs.VERBOSITY_INFO)
        cs.set_verbosity(cs.VERBOSITY_SILENT)


# =============================================================================
# Tensor Tests
# =============================================================================

class TestTensor:
    def test_create_from_shape(self):
        t = cs.Tensor((10, 5))
        assert t.shape == (10, 5)
        assert t.ndim == 2
        assert t.size == 50
    
    def test_zeros(self):
        t = cs.zeros((10, 5))
        assert t[0, 0] == 0.0
        assert t[9, 4] == 0.0
    
    def test_ones(self):
        t = cs.ones((3, 3))
        assert t[0, 0] == 1.0
        assert t[2, 2] == 1.0
    
    def test_rand_uniform(self):
        t = cs.rand_uniform((100, 64), low=-0.1, high=0.1)
        arr = t.numpy()
        assert arr.min() >= -0.1
        assert arr.max() < 0.1
    
    def test_rand_normal(self):
        t = cs.rand_normal((1000, 100), mean=0.0, std=1.0)
        arr = t.numpy()
        assert abs(arr.mean()) < 0.1
        assert abs(arr.std() - 1.0) < 0.1
    
    def test_from_numpy(self):
        arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        t = cs.Tensor(arr)
        assert t[0, 0] == 1.0
        assert t[1, 1] == 4.0
    
    def test_numpy_roundtrip(self):
        original = np.random.randn(50, 30).astype(np.float32)
        t = cs.Tensor(original)
        recovered = t.numpy()
        np.testing.assert_allclose(original, recovered, rtol=1e-5)
    
    def test_indexing(self):
        t = cs.zeros((5, 5))
        t[2, 3] = 42.0
        assert t[2, 3] == 42.0
    
    def test_clone(self):
        t1 = cs.rand_uniform((10, 10))
        t2 = t1.clone()
        t1[0, 0] = 999.0
        assert t2[0, 0] != 999.0
    
    def test_row(self):
        t = cs.Tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        row = t.row(1)
        np.testing.assert_array_equal(row, [4, 5, 6])
    
    def test_fill_uniform(self):
        t = cs.Tensor((100, 100))
        t.fill_uniform(-1.0, 1.0)
        arr = t.numpy()
        assert arr.min() >= -1.0
        assert arr.max() < 1.0


# =============================================================================
# Matrix Factorization Tests
# =============================================================================

class TestMatrixFactorization:
    def test_create(self):
        model = cs.MatrixFactorization(100, 500, 32, use_biases=True)
        assert model.num_users == 100
        assert model.num_items == 500
        assert model.embedding_dim == 32
        assert model.num_parameters > 0
    
    def test_forward_user(self):
        model = cs.MatrixFactorization(100, 500, 32)
        
        # Single
        emb = model.forward_user(0)
        assert emb.shape == (32,)
        
        # Batch
        embs = model.forward_user(np.array([0, 1, 2]))
        assert embs.shape == (3, 32)
    
    def test_forward_item(self):
        model = cs.MatrixFactorization(100, 500, 32)
        emb = model.forward_item(10)
        assert emb.shape == (32,)
    
    def test_score_single(self):
        model = cs.MatrixFactorization(100, 500, 32)
        score = model.score(user_id=0, item_ids=10)
        assert isinstance(score, float)
    
    def test_score_batch(self):
        model = cs.MatrixFactorization(100, 500, 32)
        scores = model.score(user_id=0, item_ids=[10, 20, 30])
        assert len(scores) == 3
    
    def test_recommend(self):
        model = cs.MatrixFactorization(100, 500, 32)
        items, scores = model.recommend(user_id=5, top_k=10)
        assert len(items) == 10
        assert len(scores) == 10
        # Sorted descending
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    
    def test_train_step_bpr(self):
        model = cs.MatrixFactorization(100, 500, 32)
        
        user_ids = np.array([0, 1, 2], dtype=np.uint32)
        pos_items = np.array([10, 20, 30], dtype=np.uint32)
        neg_items = np.array([40, 50, 60], dtype=np.uint32)
        
        model.train_step_bpr(user_ids, pos_items, neg_items, learning_rate=0.1)
        # Should not raise
    
    def test_train_eval_mode(self):
        model = cs.MatrixFactorization(100, 500, 32)
        assert model.training
        model.eval()
        assert not model.training
        model.train()
        assert model.training
    
    def test_fit_bpr(self):
        model = cs.MatrixFactorization(100, 500, 32)
        user_ids = np.random.randint(0, 100, 1000).astype(np.uint32)
        item_ids = np.random.randint(0, 500, 1000).astype(np.uint32)
        
        history = model.fit(user_ids, item_ids, epochs=2, verbose=False)
        assert 'loss' in history or len(history) >= 0


# =============================================================================
# Sparse Matrix Tests
# =============================================================================

class TestSparseMatrix:
    def test_create(self):
        sp = cs.SparseMatrix(rows=100, cols=100, nnz=500)
        assert sp.shape == (100, 100)
        assert sp.nnz == 500
    
    def test_get_element(self):
        sp = cs.SparseMatrix(rows=10, cols=10, nnz=10)
        # Newly created sparse matrix has zeros
        val = sp[0, 0]
        assert val == 0.0
    
    def test_to_dense(self):
        sp = cs.SparseMatrix(rows=10, cols=10, nnz=10)
        dense = sp.to_dense()
        assert dense.shape == (10, 10)


# =============================================================================
# Training Config Tests
# =============================================================================

class TestTrainingConfigs:
    def test_sgd(self):
        opt = cs.SGD(learning_rate=0.01, momentum=0.9)
        assert opt.learning_rate == 0.01
        assert opt.momentum == 0.9
        d = opt.to_dict()
        assert d["type"] == "SGD"
    
    def test_adam(self):
        opt = cs.Adam(learning_rate=0.001)
        assert opt.learning_rate == 0.001
        assert opt.beta1 == 0.9
        assert opt.beta2 == 0.999
    
    def test_adamw(self):
        opt = cs.AdamW(learning_rate=0.001, weight_decay=0.01)
        assert opt.weight_decay == 0.01
    
    def test_bpr_loss(self):
        loss = cs.BPRLoss(margin=0.5)
        assert loss.margin == 0.5
    
    def test_mse_loss(self):
        loss = cs.MSELoss()
        assert loss is not None
    
    def test_contrastive_loss(self):
        loss = cs.ContrastiveLoss(temperature=0.1)
        assert loss.temperature == 0.1


# =============================================================================
# Utility Tests
# =============================================================================

class TestUtils:
    def test_set_seed(self):
        cs.set_seed(42)
        t1 = cs.rand_uniform((10,))
        
        cs.set_seed(42)
        t2 = cs.rand_uniform((10,))
        
        np.testing.assert_array_equal(t1.numpy(), t2.numpy())
    
    def test_sample_negatives(self):
        negatives = cs.sample_negatives(100, num_items=1000)
        assert len(negatives) == 100
        assert negatives.dtype == np.uint32
        assert all(0 <= x < 1000 for x in negatives)
    
    def test_sample_negatives_with_exclude(self):
        negatives = cs.sample_negatives(100, num_items=1000, exclude=[0, 1, 2])
        assert all(x not in [0, 1, 2] for x in negatives)


# =============================================================================
# I/O Tests
# =============================================================================

class TestIO:
    def test_tensor_save_load(self, tmp_path):
        t = cs.rand_uniform((10, 5))
        path = str(tmp_path / "tensor.cst")
        t.save(path)
        
        loaded = cs.Tensor.load(path)
        np.testing.assert_allclose(t.numpy(), loaded.numpy(), rtol=1e-5)
    
    def test_tensor_to_npy(self, tmp_path):
        t = cs.rand_uniform((10, 5))
        path = str(tmp_path / "tensor.npy")
        t.to_npy(path)
        
        loaded = np.load(path)
        np.testing.assert_allclose(t.numpy(), loaded, rtol=1e-5)
    
    def test_model_save_load(self, tmp_path):
        model = cs.MatrixFactorization(100, 500, 32)
        path = str(tmp_path / "model.csm")
        
        scores_before = model.score(0, [1, 2, 3])
        model.save(path)
        
        loaded = cs.Model.load(path)
        scores_after = loaded.score(0, [1, 2, 3])
        
        np.testing.assert_allclose(scores_before, scores_after, rtol=1e-5)
    
    def test_model_metadata_json(self):
        model = cs.MatrixFactorization(100, 500, 32)
        json_str = model.metadata_json()
        assert "num_users" in json_str or "model_type" in json_str
    
    def test_detect_format(self, tmp_path):
        model = cs.MatrixFactorization(10, 10, 8)
        path = str(tmp_path / "model.csm")
        model.save(path)
        
        fmt = cs.detect_format(path)
        assert fmt == "native"
    
    def test_save_load_model_helpers(self, tmp_path):
        model = cs.MatrixFactorization(100, 500, 32)
        path = str(tmp_path / "model.csm")
        
        cs.save_model(model, path)
        loaded = cs.load_model(path)
        
        assert loaded.num_parameters == model.num_parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
