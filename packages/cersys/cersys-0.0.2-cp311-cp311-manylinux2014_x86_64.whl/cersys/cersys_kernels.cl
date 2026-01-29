// =============================================================================
// Cersys OpenCL Kernels
// High-performance GPU kernels for recommender system operations
// 
// This file is kept in sync with the embedded kernels in cs_gpu.c
// Last sync: January 2026
// =============================================================================

#define TILE_SIZE 16
#define VECTOR_WIDTH 4

// =============================================================================
// MATRIX MULTIPLICATION
// =============================================================================

// Simple matrix multiply: C[M,N] = A[M,K] @ B[K,N]^T (B transposed)
// Used for small matrices where tiling overhead isn't worth it
__kernel void matmul_simple(
    __global const float *A,        // [M, K]
    __global const float *B,        // [N, K] (stored transposed for cache efficiency)
    __global float *C,              // [M, N]
    const int M,
    const int K,
    const int N
) {
    int row = get_global_id(0);
    int col = get_global_id(1);
    
    if (row < M && col < N) {
        float sum = 0.0f;
        
        // Unroll by 4 for better ILP
        int k = 0;
        for (; k + 3 < K; k += 4) {
            sum += A[row * K + k]     * B[col * K + k];
            sum += A[row * K + k + 1] * B[col * K + k + 1];
            sum += A[row * K + k + 2] * B[col * K + k + 2];
            sum += A[row * K + k + 3] * B[col * K + k + 3];
        }
        // Handle remainder
        for (; k < K; k++) {
            sum += A[row * K + k] * B[col * K + k];
        }
        
        C[row * N + col] = sum;
    }
}

// Tiled matrix multiply with local memory for large matrices
// Uses 16x16 tiles for optimal occupancy on most GPUs
__kernel void matmul_tiled(
    __global const float *A,        // [M, K]
    __global const float *B,        // [N, K] (stored transposed)
    __global float *C,              // [M, N]
    const int M,
    const int K,
    const int N,
    __local float *A_tile,          // [TILE_SIZE * TILE_SIZE]
    __local float *B_tile           // [TILE_SIZE * TILE_SIZE]
) {
    int row = get_global_id(0);
    int col = get_global_id(1);
    int local_row = get_local_id(0);
    int local_col = get_local_id(1);
    
    float sum = 0.0f;
    int num_tiles = (K + TILE_SIZE - 1) / TILE_SIZE;
    
    for (int t = 0; t < num_tiles; t++) {
        // Cooperative tile loading
        int a_col = t * TILE_SIZE + local_col;
        int b_col = t * TILE_SIZE + local_col;
        
        A_tile[local_row * TILE_SIZE + local_col] = 
            (row < M && a_col < K) ? A[row * K + a_col] : 0.0f;
        B_tile[local_row * TILE_SIZE + local_col] = 
            (col < N && b_col < K) ? B[col * K + b_col] : 0.0f;
        
        barrier(CLK_LOCAL_MEM_FENCE);
        
        // Compute partial dot product with manual unroll
        #pragma unroll 4
        for (int k = 0; k < TILE_SIZE; k++) {
            sum += A_tile[local_row * TILE_SIZE + k] * B_tile[local_col * TILE_SIZE + k];
        }
        
        barrier(CLK_LOCAL_MEM_FENCE);
    }
    
    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}

// =============================================================================
// DENSE LAYER FORWARD
// output = input @ weights^T + bias
// =============================================================================

__kernel void dense_forward(
    __global const float *input,    // [batch, in_features]
    __global const float *weights,  // [out_features, in_features]
    __global const float *bias,     // [out_features] or NULL
    __global float *output,         // [batch, out_features]
    const int batch_size,
    const int in_features,
    const int out_features,
    const int use_bias
) {
    int batch = get_global_id(0);
    int out_idx = get_global_id(1);
    
    if (batch < batch_size && out_idx < out_features) {
        float sum = 0.0f;
        
        // Vectorized accumulation where possible
        int i = 0;
        for (; i + 3 < in_features; i += 4) {
            sum += input[batch * in_features + i]     * weights[out_idx * in_features + i];
            sum += input[batch * in_features + i + 1] * weights[out_idx * in_features + i + 1];
            sum += input[batch * in_features + i + 2] * weights[out_idx * in_features + i + 2];
            sum += input[batch * in_features + i + 3] * weights[out_idx * in_features + i + 3];
        }
        for (; i < in_features; i++) {
            sum += input[batch * in_features + i] * weights[out_idx * in_features + i];
        }
        
        if (use_bias) sum += bias[out_idx];
        output[batch * out_features + out_idx] = sum;
    }
}

// Dense forward with fused ReLU activation
__kernel void dense_forward_relu(
    __global const float *input,
    __global const float *weights,
    __global const float *bias,
    __global float *output,
    const int batch_size,
    const int in_features,
    const int out_features,
    const int use_bias
) {
    int batch = get_global_id(0);
    int out_idx = get_global_id(1);
    
    if (batch < batch_size && out_idx < out_features) {
        float sum = 0.0f;
        
        int i = 0;
        for (; i + 3 < in_features; i += 4) {
            sum += input[batch * in_features + i]     * weights[out_idx * in_features + i];
            sum += input[batch * in_features + i + 1] * weights[out_idx * in_features + i + 1];
            sum += input[batch * in_features + i + 2] * weights[out_idx * in_features + i + 2];
            sum += input[batch * in_features + i + 3] * weights[out_idx * in_features + i + 3];
        }
        for (; i < in_features; i++) {
            sum += input[batch * in_features + i] * weights[out_idx * in_features + i];
        }
        
        if (use_bias) sum += bias[out_idx];
        
        // Fused ReLU
        output[batch * out_features + out_idx] = fmax(0.0f, sum);
    }
}

// =============================================================================
// EMBEDDING LOOKUP
// =============================================================================

__kernel void embedding_lookup(
    __global const float *table,    // [num_embeddings, dim]
    __global const uint *indices,   // [batch_size]
    __global float *output,         // [batch_size, dim]
    const int dim,
    const int batch_size,
    const int num_embeddings
) {
    int batch = get_global_id(0);
    int d = get_global_id(1);
    
    if (batch < batch_size && d < dim) {
        uint idx = indices[batch];
        if (idx < num_embeddings) {
            output[batch * dim + d] = table[idx * dim + d];
        }
    }
}

// =============================================================================
// DOT PRODUCT / SCORING
// =============================================================================

// Batched dot product: output[i] = sum(A[i,:] * B[i,:])
__kernel void batched_dot_product(
    __global const float *A,        // [batch, dim]
    __global const float *B,        // [batch, dim]
    __global float *scores,         // [batch]
    const int batch_size,
    const int dim
) {
    int batch = get_global_id(0);
    
    if (batch < batch_size) {
        float sum = 0.0f;
        int base = batch * dim;
        
        // Unroll for ILP
        int d = 0;
        for (; d + 3 < dim; d += 4) {
            sum += A[base + d]     * B[base + d];
            sum += A[base + d + 1] * B[base + d + 1];
            sum += A[base + d + 2] * B[base + d + 2];
            sum += A[base + d + 3] * B[base + d + 3];
        }
        for (; d < dim; d++) {
            sum += A[base + d] * B[base + d];
        }
        
        scores[batch] = sum;
    }
}

// Score user against all items: scores[i] = dot(user, items[i])
__kernel void score_all_items(
    __global const float *user_emb,     // [dim]
    __global const float *item_embs,    // [num_items, dim]
    __global float *scores,             // [num_items]
    const int num_items,
    const int dim
) {
    int item = get_global_id(0);
    
    if (item < num_items) {
        float sum = 0.0f;
        int base = item * dim;
        
        int d = 0;
        for (; d + 3 < dim; d += 4) {
            sum += user_emb[d]     * item_embs[base + d];
            sum += user_emb[d + 1] * item_embs[base + d + 1];
            sum += user_emb[d + 2] * item_embs[base + d + 2];
            sum += user_emb[d + 3] * item_embs[base + d + 3];
        }
        for (; d < dim; d++) {
            sum += user_emb[d] * item_embs[base + d];
        }
        
        scores[item] = sum;
    }
}

// Batched scoring with embedding table lookup
__kernel void batched_score(
    __global const float *user_emb_table,  // [num_users, dim]
    __global const float *item_emb_table,  // [num_items, dim]
    __global const float *item_biases,     // [num_items] or NULL
    __global const uint *user_ids,         // [batch_size]
    __global const uint *item_ids,         // [batch_size]
    __global float *scores,                // [batch_size] output
    const int dim,
    const int batch_size,
    const int use_biases
) {
    int b = get_global_id(0);
    if (b >= batch_size) return;
    
    uint u = user_ids[b];
    uint i = item_ids[b];
    
    __global const float *u_vec = user_emb_table + u * dim;
    __global const float *i_vec = item_emb_table + i * dim;
    
    float score = 0.0f;
    int d = 0;
    for (; d + 3 < dim; d += 4) {
        score += u_vec[d]     * i_vec[d];
        score += u_vec[d + 1] * i_vec[d + 1];
        score += u_vec[d + 2] * i_vec[d + 2];
        score += u_vec[d + 3] * i_vec[d + 3];
    }
    for (; d < dim; d++) {
        score += u_vec[d] * i_vec[d];
    }
    
    if (use_biases && item_biases) {
        score += item_biases[i];
    }
    
    scores[b] = score;
}

// =============================================================================
// ACTIVATION FUNCTIONS
// =============================================================================

__kernel void relu(__global float *data, const int size) {
    int idx = get_global_id(0);
    if (idx < size) {
        data[idx] = fmax(0.0f, data[idx]);
    }
}

__kernel void leaky_relu(__global float *data, const int size, const float slope) {
    int idx = get_global_id(0);
    if (idx < size) {
        float x = data[idx];
        data[idx] = x > 0.0f ? x : slope * x;
    }
}

__kernel void sigmoid(__global float *data, const int size) {
    int idx = get_global_id(0);
    if (idx < size) {
        // Numerically stable sigmoid
        float x = data[idx];
        if (x >= 0.0f) {
            data[idx] = 1.0f / (1.0f + exp(-x));
        } else {
            float ex = exp(x);
            data[idx] = ex / (1.0f + ex);
        }
    }
}

__kernel void tanh_act(__global float *data, const int size) {
    int idx = get_global_id(0);
    if (idx < size) {
        data[idx] = tanh(data[idx]);
    }
}

// GELU: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
__kernel void gelu(__global float *data, const int size) {
    int idx = get_global_id(0);
    if (idx < size) {
        float x = data[idx];
        // sqrt(2/pi) ≈ 0.7978845608
        float inner = 0.7978845608f * (x + 0.044715f * x * x * x);
        data[idx] = 0.5f * x * (1.0f + tanh(inner));
    }
}

// =============================================================================
// VECTOR OPERATIONS (BLAS-like)
// =============================================================================

// Vector add: C = A + B
__kernel void vec_add(
    __global const float *A,
    __global const float *B,
    __global float *C,
    const int size
) {
    int idx = get_global_id(0);
    if (idx < size) {
        C[idx] = A[idx] + B[idx];
    }
}

// Vectorized add using float4
__kernel void vec_add_vec4(
    __global const float4 *A,
    __global const float4 *B,
    __global float4 *C,
    const int size4
) {
    int idx = get_global_id(0);
    if (idx < size4) {
        C[idx] = A[idx] + B[idx];
    }
}

// Vector scale: A = A * scale
__kernel void vec_scale(__global float *data, const float scale, const int size) {
    int idx = get_global_id(0);
    if (idx < size) {
        data[idx] *= scale;
    }
}

// Vector AXPY: Y = alpha * X + Y
__kernel void vec_axpy(const float alpha, __global const float *X, __global float *Y, const int size) {
    int idx = get_global_id(0);
    if (idx < size) {
        Y[idx] += alpha * X[idx];
    }
}

// Vectorized AXPY using float4
__kernel void vec_axpy_vec4(
    const float alpha,
    __global const float4 *X,
    __global float4 *Y,
    const int size4
) {
    int idx = get_global_id(0);
    if (idx < size4) {
        Y[idx] += alpha * X[idx];
    }
}

// =============================================================================
// SOFTMAX
// =============================================================================

// Row-wise softmax with numerical stability
__kernel void softmax_rows(__global float *data, const int rows, const int cols) {
    int row = get_global_id(0);
    
    if (row < rows) {
        int base = row * cols;
        
        // Find max for numerical stability
        float max_val = -INFINITY;
        for (int c = 0; c < cols; c++) {
            float v = data[base + c];
            if (v > max_val) max_val = v;
        }
        
        // Compute exp and sum
        float sum = 0.0f;
        for (int c = 0; c < cols; c++) {
            float v = exp(data[base + c] - max_val);
            data[base + c] = v;
            sum += v;
        }
        
        // Normalize
        float inv_sum = 1.0f / sum;
        for (int c = 0; c < cols; c++) {
            data[base + c] *= inv_sum;
        }
    }
}

// =============================================================================
// COSINE SIMILARITY
// =============================================================================

__kernel void cosine_similarity(
    __global const float *A,        // [batch, dim]
    __global const float *B,        // [batch, dim]
    __global float *scores,         // [batch]
    const int batch_size,
    const int dim
) {
    int batch = get_global_id(0);
    
    if (batch < batch_size) {
        float dot = 0.0f;
        float norm_a = 0.0f;
        float norm_b = 0.0f;
        int base = batch * dim;
        
        for (int d = 0; d < dim; d++) {
            float a = A[base + d];
            float b = B[base + d];
            dot += a * b;
            norm_a += a * a;
            norm_b += b * b;
        }
        
        float denom = sqrt(norm_a) * sqrt(norm_b);
        scores[batch] = denom > 1e-8f ? dot / denom : 0.0f;
    }
}

// =============================================================================
// LAYER NORMALIZATION
// =============================================================================

__kernel void layer_norm(
    __global float *data,           // [batch, features] - modified in place
    __global const float *gamma,    // [features]
    __global const float *beta,     // [features]
    const int batch_size,
    const int features,
    const float epsilon
) {
    int batch = get_global_id(0);
    
    if (batch < batch_size) {
        int base = batch * features;
        
        // Compute mean (Welford's online algorithm for stability)
        float mean = 0.0f;
        for (int f = 0; f < features; f++) {
            mean += data[base + f];
        }
        mean /= features;
        
        // Compute variance
        float var = 0.0f;
        for (int f = 0; f < features; f++) {
            float diff = data[base + f] - mean;
            var += diff * diff;
        }
        var /= features;
        
        // Normalize and apply affine transform
        float inv_std = rsqrt(var + epsilon);  // rsqrt is faster than 1/sqrt
        for (int f = 0; f < features; f++) {
            float x = data[base + f];
            float norm = (x - mean) * inv_std;
            data[base + f] = gamma[f] * norm + beta[f];
        }
    }
}

// =============================================================================
// BPR TRAINING KERNELS
// =============================================================================

// Single-sample BPR gradient update (DEPRECATED - use bpr_batch_update)
// This kernel assumes sigmoid gradient has been precomputed by the host
__kernel void bpr_gradient_update(
    __global float *user_emb,       // [dim]
    __global float *pos_emb,        // [dim]
    __global float *neg_emb,        // [dim]
    const float lr,
    const float reg,
    const int dim
) {
    int d = get_global_id(0);
    
    if (d < dim) {
        float u = user_emb[d];
        float p = pos_emb[d];
        float n = neg_emb[d];
        
        // BPR update: gradient is sigmoid(-x_uij) * (p - n) for user
        // Weight decay applied, sigmoid was computed on host
        float decay = 1.0f - lr * reg;
        user_emb[d] = u * decay + lr * (p - n);
        pos_emb[d] = p * decay + lr * u;
        neg_emb[d] = n * decay - lr * u;
    }
}

// Batched BPR training kernel - processes entire batch in parallel
// This is the preferred kernel for BPR training
__kernel void bpr_batch_update(
    __global float *user_emb_table,   // [num_users, dim]
    __global float *item_emb_table,   // [num_items, dim]
    __global float *item_biases,      // [num_items] or dummy if not used
    __global const uint *user_ids,    // [batch_size]
    __global const uint *pos_item_ids,// [batch_size]
    __global const uint *neg_item_ids,// [batch_size]
    const float lr,
    const float reg,
    const int dim,
    const int batch_size,
    const int use_biases
) {
    int b = get_global_id(0);  // batch index
    if (b >= batch_size) return;
    
    uint u = user_ids[b];
    uint pos_i = pos_item_ids[b];
    uint neg_i = neg_item_ids[b];
    
    __global float *u_vec = user_emb_table + u * dim;
    __global float *pos_vec = item_emb_table + pos_i * dim;
    __global float *neg_vec = item_emb_table + neg_i * dim;
    
    // Compute scores with loop unrolling
    float pos_score = 0.0f;
    float neg_score = 0.0f;
    
    int d = 0;
    for (; d + 3 < dim; d += 4) {
        pos_score += u_vec[d]     * pos_vec[d];
        pos_score += u_vec[d + 1] * pos_vec[d + 1];
        pos_score += u_vec[d + 2] * pos_vec[d + 2];
        pos_score += u_vec[d + 3] * pos_vec[d + 3];
        
        neg_score += u_vec[d]     * neg_vec[d];
        neg_score += u_vec[d + 1] * neg_vec[d + 1];
        neg_score += u_vec[d + 2] * neg_vec[d + 2];
        neg_score += u_vec[d + 3] * neg_vec[d + 3];
    }
    for (; d < dim; d++) {
        pos_score += u_vec[d] * pos_vec[d];
        neg_score += u_vec[d] * neg_vec[d];
    }
    
    // Add biases if enabled
    if (use_biases) {
        pos_score += item_biases[pos_i];
        neg_score += item_biases[neg_i];
    }
    
    // BPR gradient: compute sigmoid(-x_uij) with numerical stability
    float x_uij = pos_score - neg_score;
    float sigmoid_neg;
    if (x_uij > 35.0f) {
        sigmoid_neg = 0.0f;      // sigmoid(-x) ≈ 0 for large x
    } else if (x_uij < -35.0f) {
        sigmoid_neg = 1.0f;      // sigmoid(-x) ≈ 1 for very negative x
    } else {
        sigmoid_neg = 1.0f / (1.0f + exp(x_uij));
    }
    
    // Update embeddings
    // Note: Using non-atomic updates. Collisions are rare with large
    // embedding tables and random sampling; gradient averaging occurs naturally.
    for (d = 0; d < dim; d++) {
        float u_d = u_vec[d];
        float pos_d = pos_vec[d];
        float neg_d = neg_vec[d];
        
        // Gradients: loss = -log(sigmoid(x_uij)) + reg/2 * ||params||^2
        float u_grad = sigmoid_neg * (neg_d - pos_d) + reg * u_d;
        float pos_grad = sigmoid_neg * (-u_d) + reg * pos_d;
        float neg_grad = sigmoid_neg * u_d + reg * neg_d;
        
        u_vec[d] -= lr * u_grad;
        pos_vec[d] -= lr * pos_grad;
        neg_vec[d] -= lr * neg_grad;
    }
    
    // Update biases if enabled
    if (use_biases) {
        // Bias gradient: sigmoid(-x_uij) for pos, -sigmoid(-x_uij) for neg
        item_biases[pos_i] += lr * sigmoid_neg;
        item_biases[neg_i] -= lr * sigmoid_neg;
    }
}

// =============================================================================
// REDUCTION KERNELS (for loss computation)
// =============================================================================

// Parallel sum reduction
__kernel void reduce_sum(
    __global const float *input,
    __global float *output,
    __local float *scratch,
    const int n
) {
    int gid = get_global_id(0);
    int lid = get_local_id(0);
    int group_size = get_local_size(0);
    
    // Load into local memory
    scratch[lid] = (gid < n) ? input[gid] : 0.0f;
    barrier(CLK_LOCAL_MEM_FENCE);
    
    // Parallel reduction in local memory
    for (int stride = group_size / 2; stride > 0; stride >>= 1) {
        if (lid < stride) {
            scratch[lid] += scratch[lid + stride];
        }
        barrier(CLK_LOCAL_MEM_FENCE);
    }
    
    // Write result
    if (lid == 0) {
        output[get_group_id(0)] = scratch[0];
    }
}

// Find maximum (for softmax numerical stability)
__kernel void reduce_max(
    __global const float *input,
    __global float *output,
    __local float *scratch,
    const int n
) {
    int gid = get_global_id(0);
    int lid = get_local_id(0);
    int group_size = get_local_size(0);
    
    scratch[lid] = (gid < n) ? input[gid] : -INFINITY;
    barrier(CLK_LOCAL_MEM_FENCE);
    
    for (int stride = group_size / 2; stride > 0; stride >>= 1) {
        if (lid < stride) {
            scratch[lid] = fmax(scratch[lid], scratch[lid + stride]);
        }
        barrier(CLK_LOCAL_MEM_FENCE);
    }
    
    if (lid == 0) {
        output[get_group_id(0)] = scratch[0];
    }
}
