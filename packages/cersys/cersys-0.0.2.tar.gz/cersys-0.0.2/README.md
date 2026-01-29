# Cersys

[![PyPI](https://img.shields.io/pypi/v/cersys)](https://pypi.org/project/cersys/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

High-performance recommender systems library with GPU acceleration.

## Installation

```bash
pip install cersys
```

**Requirements:** Python 3.8+ and OpenCL runtime (included on macOS; on Linux: `sudo apt install ocl-icd-libopencl1`)

## Quick Start

```python
import cersys as cs

cs.init()

# Create a matrix factorization model
model = cs.MatrixFactorization(
    num_users=10000,
    num_items=50000,
    embedding_dim=64,
)

# Train on user-item interactions
model.fit(user_ids, item_ids, epochs=10)

# Get recommendations
items, scores = model.recommend(user_id=42, top_k=10)

# Score specific items
score = model.score(user_id=42, item_ids=[1, 2, 3])

cs.shutdown()
```

## Features

- **Matrix Factorization** with BPR and ALS training
- **GPU acceleration** via OpenCL (automatic CPU fallback)
- **Fast inference** with BLAS-optimized scoring
- **Simple API** with NumPy interoperability

## Links

- [GitHub](https://github.com/22cav/cersys)
- [Documentation](https://github.com/22cav/cersys#readme)
