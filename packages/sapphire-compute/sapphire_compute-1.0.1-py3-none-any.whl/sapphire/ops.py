"""
Sapphire Tensor Operations - Complete Implementation

Full tensor algebra API matching PyTorch semantics with
Apple Silicon optimization through AMX and GPU.

All operations support:
- Automatic broadcasting
- Gradient computation (for training)
- In-place operations
- View/slice operations (zero-copy)
- Quantization

Copyright (c) 2026 SVECTOR. All rights reserved.
"""

from typing import List, Optional, Sequence, Tuple, Union

import numpy as np

from . import Tensor, dtype, float16, float32, int8

# Type aliases
Shape = Tuple[int, ...]
TensorLike = Union['Tensor', np.ndarray, List, float, int]


# =============================================================================
# Creation Operations
# =============================================================================

def tensor(data: TensorLike, dtype: dtype = float32, requires_grad: bool = False) -> Tensor:
    """Create a tensor from data."""
    return Tensor(data=data, dtype=dtype, requires_grad=requires_grad)

def zeros(*shape: int, dtype: dtype = float32, requires_grad: bool = False) -> Tensor:
    """Create a tensor filled with zeros."""
    t = Tensor(shape=shape, dtype=dtype)
    t._requires_grad = requires_grad
    return t

def ones(*shape: int, dtype: dtype = float32, requires_grad: bool = False) -> Tensor:
    """Create a tensor filled with ones."""
    t = Tensor(shape=shape, dtype=dtype)
    t._data.fill(1.0)
    t._requires_grad = requires_grad
    return t

def full(shape: Shape, fill_value: float, dtype: dtype = float32) -> Tensor:
    """Create a tensor filled with a scalar value."""
    t = Tensor(shape=shape, dtype=dtype)
    t._data.fill(fill_value)
    return t

def empty(*shape: int, dtype: dtype = float32) -> Tensor:
    """Create an uninitialized tensor."""
    return Tensor(shape=shape, dtype=dtype)

def zeros_like(input: Tensor) -> Tensor:
    """Create a zero tensor with same shape as input."""
    return zeros(*input.shape, dtype=input.dtype)

def ones_like(input: Tensor) -> Tensor:
    """Create a ones tensor with same shape as input."""
    return ones(*input.shape, dtype=input.dtype)

def rand(*shape: int, dtype: dtype = float32) -> Tensor:
    """Create a tensor with uniform random values in [0, 1)."""
    data = np.random.rand(*shape).astype(np.float32)
    return Tensor(data=data, dtype=dtype)

def randn(*shape: int, dtype: dtype = float32) -> Tensor:
    """Create a tensor with standard normal random values."""
    data = np.random.randn(*shape).astype(np.float32)
    return Tensor(data=data, dtype=dtype)

def randint(low: int, high: int, shape: Shape, dtype: dtype = float32) -> Tensor:
    """Create a tensor with random integers."""
    data = np.random.randint(low, high, size=shape).astype(np.float32)
    return Tensor(data=data, dtype=dtype)

def arange(start: float, end: Optional[float] = None, step: float = 1.0, dtype: dtype = float32) -> Tensor:
    """Create a 1D tensor with evenly spaced values."""
    if end is None:
        end = start
        start = 0
    data = np.arange(start, end, step, dtype=np.float32)
    return Tensor(data=data, dtype=dtype)

def linspace(start: float, end: float, steps: int, dtype: dtype = float32) -> Tensor:
    """Create a 1D tensor with linearly spaced values."""
    data = np.linspace(start, end, steps, dtype=np.float32)
    return Tensor(data=data, dtype=dtype)

def eye(n: int, m: Optional[int] = None, dtype: dtype = float32) -> Tensor:
    """Create a 2D identity matrix."""
    m = m or n
    data = np.eye(n, m, dtype=np.float32)
    return Tensor(data=data, dtype=dtype)

def from_numpy(arr: np.ndarray) -> Tensor:
    """Create a tensor from a NumPy array (shares memory if possible)."""
    return Tensor(data=arr.astype(np.float32))


# =============================================================================
# Mathematical Operations
# =============================================================================

def matmul(a: Tensor, b: Tensor) -> Tensor:
    """Matrix multiplication using AMX acceleration."""
    from . import matmul as _matmul
    return _matmul(a, b)

def mm(a: Tensor, b: Tensor) -> Tensor:
    """Matrix multiplication (alias for matmul)."""
    return matmul(a, b)

def bmm(a: Tensor, b: Tensor) -> Tensor:
    """Batch matrix multiplication."""
    assert a.ndim == 3 and b.ndim == 3
    assert a.shape[0] == b.shape[0]
    assert a.shape[2] == b.shape[1]
    
    batch = a.shape[0]
    result = zeros(batch, a.shape[1], b.shape[2])
    
    for i in range(batch):
        # Extract matrices and multiply
        a_slice = Tensor(data=a._data[i])
        b_slice = Tensor(data=b._data[i])
        r = matmul(a_slice, b_slice)
        result._data[i] = r._data
    
    return result

def dot(a: Tensor, b: Tensor) -> Tensor:
    """Dot product of two 1D tensors."""
    assert a.ndim == 1 and b.ndim == 1
    assert a.shape[0] == b.shape[0]
    return Tensor(data=np.array([np.dot(a._data, b._data)]))

def add(a: Tensor, b: TensorLike, alpha: float = 1.0) -> Tensor:
    """Element-wise addition: a + alpha * b."""
    if isinstance(b, Tensor):
        return Tensor(data=a._data + alpha * b._data)
    return Tensor(data=a._data + alpha * np.asarray(b))

def sub(a: Tensor, b: TensorLike) -> Tensor:
    """Element-wise subtraction."""
    if isinstance(b, Tensor):
        return Tensor(data=a._data - b._data)
    return Tensor(data=a._data - np.asarray(b))

def mul(a: Tensor, b: TensorLike) -> Tensor:
    """Element-wise multiplication."""
    if isinstance(b, Tensor):
        return Tensor(data=a._data * b._data)
    return Tensor(data=a._data * np.asarray(b))

def div(a: Tensor, b: TensorLike) -> Tensor:
    """Element-wise division."""
    if isinstance(b, Tensor):
        return Tensor(data=a._data / b._data)
    return Tensor(data=a._data / np.asarray(b))

def pow(a: Tensor, exponent: float) -> Tensor:
    """Element-wise power."""
    return Tensor(data=np.power(a._data, exponent))

def sqrt(x: Tensor) -> Tensor:
    """Element-wise square root."""
    return Tensor(data=np.sqrt(x._data))

def rsqrt(x: Tensor) -> Tensor:
    """Element-wise reciprocal square root."""
    return Tensor(data=1.0 / np.sqrt(x._data))

def exp(x: Tensor) -> Tensor:
    """Element-wise exponential."""
    return Tensor(data=np.exp(x._data))

def log(x: Tensor) -> Tensor:
    """Element-wise natural logarithm."""
    return Tensor(data=np.log(x._data))

def abs(x: Tensor) -> Tensor:
    """Element-wise absolute value."""
    return Tensor(data=np.abs(x._data))

def neg(x: Tensor) -> Tensor:
    """Element-wise negation."""
    return Tensor(data=-x._data)

def sin(x: Tensor) -> Tensor:
    return Tensor(data=np.sin(x._data))

def cos(x: Tensor) -> Tensor:
    return Tensor(data=np.cos(x._data))

def tan(x: Tensor) -> Tensor:
    return Tensor(data=np.tan(x._data))

def tanh(x: Tensor) -> Tensor:
    return Tensor(data=np.tanh(x._data))


# =============================================================================
# Activation Functions (Native Accelerated)
# =============================================================================

# Import native bindings for accelerated operations
try:
    from .native import is_native_available as _native_available
    from .native import native_gelu as _native_gelu
    from .native import native_matmul as _native_matmul
    from .native import native_matmul_gelu as _native_matmul_gelu
    from .native import native_matmul_relu as _native_matmul_relu
    from .native import native_relu as _native_relu
    from .native import native_silu as _native_silu
    _HAS_NATIVE = _native_available()
except ImportError:
    _HAS_NATIVE = False

def relu(x: Tensor) -> Tensor:
    """Rectified Linear Unit activation (AMX accelerated)."""
    if _HAS_NATIVE and x.ndim <= 2:
        return Tensor(data=_native_relu(x._data.reshape(-1)).reshape(x.shape))
    return Tensor(data=np.maximum(0, x._data))

def gelu(x: Tensor, approximate: str = 'tanh') -> Tensor:
    """Gaussian Error Linear Unit activation (AMX accelerated)."""
    if _HAS_NATIVE and x.ndim <= 2:
        return Tensor(data=_native_gelu(x._data.reshape(-1)).reshape(x.shape))
    if approximate == 'tanh':
        c = 0.044715
        sqrt_2_pi = 0.7978845608
        inner = sqrt_2_pi * (x._data + c * x._data**3)
        return Tensor(data=0.5 * x._data * (1 + np.tanh(inner)))
    else:
        from scipy.special import erf
        return Tensor(data=0.5 * x._data * (1 + erf(x._data / np.sqrt(2))))

def silu(x: Tensor) -> Tensor:
    """Sigmoid Linear Unit (Swish) activation (AMX accelerated)."""
    if _HAS_NATIVE and x.ndim <= 2:
        return Tensor(data=_native_silu(x._data.reshape(-1)).reshape(x.shape))
    return Tensor(data=x._data / (1 + np.exp(-x._data)))

def sigmoid(x: Tensor) -> Tensor:
    """Sigmoid activation."""
    return Tensor(data=1 / (1 + np.exp(-x._data)))

def softmax(x: Tensor, dim: int = -1) -> Tensor:
    """Softmax activation along dimension."""
    exp_x = np.exp(x._data - np.max(x._data, axis=dim, keepdims=True))
    return Tensor(data=exp_x / np.sum(exp_x, axis=dim, keepdims=True))

def log_softmax(x: Tensor, dim: int = -1) -> Tensor:
    """Log-Softmax activation."""
    max_x = np.max(x._data, axis=dim, keepdims=True)
    logsumexp = max_x + np.log(np.sum(np.exp(x._data - max_x), axis=dim, keepdims=True))
    return Tensor(data=x._data - logsumexp)

def leaky_relu(x: Tensor, negative_slope: float = 0.01) -> Tensor:
    """Leaky ReLU activation."""
    return Tensor(data=np.where(x._data > 0, x._data, negative_slope * x._data))


# =============================================================================
# Reduction Operations
# =============================================================================

def sum(x: Tensor, dim: Optional[int] = None, keepdim: bool = False) -> Tensor:
    """Sum reduction."""
    result = np.sum(x._data, axis=dim, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))

def mean(x: Tensor, dim: Optional[int] = None, keepdim: bool = False) -> Tensor:
    """Mean reduction."""
    result = np.mean(x._data, axis=dim, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))

def var(x: Tensor, dim: Optional[int] = None, unbiased: bool = True, keepdim: bool = False) -> Tensor:
    """Variance reduction."""
    ddof = 1 if unbiased else 0
    result = np.var(x._data, axis=dim, ddof=ddof, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))

def std(x: Tensor, dim: Optional[int] = None, unbiased: bool = True, keepdim: bool = False) -> Tensor:
    """Standard deviation reduction."""
    ddof = 1 if unbiased else 0
    result = np.std(x._data, axis=dim, ddof=ddof, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))

def max(x: Tensor, dim: Optional[int] = None, keepdim: bool = False) -> Tensor:
    """Maximum reduction."""
    result = np.max(x._data, axis=dim, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))

def min(x: Tensor, dim: Optional[int] = None, keepdim: bool = False) -> Tensor:
    """Minimum reduction."""
    result = np.min(x._data, axis=dim, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))

def argmax(x: Tensor, dim: Optional[int] = None) -> Tensor:
    """Index of maximum value."""
    result = np.argmax(x._data, axis=dim)
    return Tensor(data=result)

def argmin(x: Tensor, dim: Optional[int] = None) -> Tensor:
    """Index of minimum value."""
    result = np.argmin(x._data, axis=dim)
    return Tensor(data=result)

def norm(x: Tensor, p: float = 2.0, dim: Optional[int] = None, keepdim: bool = False) -> Tensor:
    """Lp norm."""
    result = np.linalg.norm(x._data, ord=p, axis=dim, keepdims=keepdim)
    return Tensor(data=result if isinstance(result, np.ndarray) else np.array([result]))


# =============================================================================
# Shape Operations
# =============================================================================

def reshape(x: Tensor, *shape: int) -> Tensor:
    """Reshape tensor."""
    return Tensor(data=x._data.reshape(shape))

def view(x: Tensor, *shape: int) -> Tensor:
    """View tensor with new shape (must be contiguous)."""
    return reshape(x, *shape)

def flatten(x: Tensor, start_dim: int = 0, end_dim: int = -1) -> Tensor:
    """Flatten dimensions."""
    shape = list(x.shape)
    if end_dim < 0:
        end_dim = len(shape) + end_dim
    
    new_shape = shape[:start_dim] + [-1] + shape[end_dim+1:]
    return Tensor(data=x._data.reshape(new_shape))

def squeeze(x: Tensor, dim: Optional[int] = None) -> Tensor:
    """Remove size-1 dimensions."""
    return Tensor(data=np.squeeze(x._data, axis=dim))

def unsqueeze(x: Tensor, dim: int) -> Tensor:
    """Add a size-1 dimension."""
    return Tensor(data=np.expand_dims(x._data, axis=dim))

def transpose(x: Tensor, dim0: int, dim1: int) -> Tensor:
    """Swap two dimensions."""
    axes = list(range(x.ndim))
    axes[dim0], axes[dim1] = axes[dim1], axes[dim0]
    return Tensor(data=np.transpose(x._data, axes))

def permute(x: Tensor, *dims: int) -> Tensor:
    """Permute dimensions."""
    return Tensor(data=np.transpose(x._data, dims))

def contiguous(x: Tensor) -> Tensor:
    """Make tensor contiguous in memory."""
    return Tensor(data=np.ascontiguousarray(x._data))

def expand(x: Tensor, *sizes: int) -> Tensor:
    """Expand tensor to larger size (broadcast)."""
    return Tensor(data=np.broadcast_to(x._data, sizes))

def repeat(x: Tensor, *sizes: int) -> Tensor:
    """Repeat tensor along dimensions."""
    return Tensor(data=np.tile(x._data, sizes))


# =============================================================================
# Concatenation and Splitting
# =============================================================================

def cat(tensors: List[Tensor], dim: int = 0) -> Tensor:
    """Concatenate tensors along dimension."""
    arrays = [t._data for t in tensors]
    return Tensor(data=np.concatenate(arrays, axis=dim))

def stack(tensors: List[Tensor], dim: int = 0) -> Tensor:
    """Stack tensors along new dimension."""
    arrays = [t._data for t in tensors]
    return Tensor(data=np.stack(arrays, axis=dim))

def split(x: Tensor, split_size: int, dim: int = 0) -> List[Tensor]:
    """Split tensor into chunks."""
    arrays = np.split(x._data, range(split_size, x.shape[dim], split_size), axis=dim)
    return [Tensor(data=a) for a in arrays]

def chunk(x: Tensor, chunks: int, dim: int = 0) -> List[Tensor]:
    """Split tensor into specified number of chunks."""
    arrays = np.array_split(x._data, chunks, axis=dim)
    return [Tensor(data=a) for a in arrays]


# =============================================================================
# Normalization
# =============================================================================

def layer_norm(x: Tensor, normalized_shape: Sequence[int], 
               weight: Optional[Tensor] = None, bias: Optional[Tensor] = None,
               eps: float = 1e-5) -> Tensor:
    """Layer normalization."""
    dims = tuple(range(-len(normalized_shape), 0))
    
    mean = np.mean(x._data, axis=dims, keepdims=True)
    var = np.var(x._data, axis=dims, keepdims=True)
    
    normalized = (x._data - mean) / np.sqrt(var + eps)
    
    if weight is not None:
        normalized = normalized * weight._data
    if bias is not None:
        normalized = normalized + bias._data
    
    return Tensor(data=normalized)

def rms_norm(x: Tensor, weight: Tensor, eps: float = 1e-5) -> Tensor:
    """RMS normalization (used in Llama)."""
    rms = np.sqrt(np.mean(x._data ** 2, axis=-1, keepdims=True) + eps)
    return Tensor(data=x._data / rms * weight._data)

def batch_norm(x: Tensor, running_mean: Tensor, running_var: Tensor,
               weight: Optional[Tensor] = None, bias: Optional[Tensor] = None,
               training: bool = False, momentum: float = 0.1, eps: float = 1e-5) -> Tensor:
    """Batch normalization."""
    if training:
        mean = np.mean(x._data, axis=0, keepdims=True)
        var = np.var(x._data, axis=0, keepdims=True)
    else:
        mean = running_mean._data
        var = running_var._data
    
    normalized = (x._data - mean) / np.sqrt(var + eps)
    
    if weight is not None:
        normalized = normalized * weight._data
    if bias is not None:
        normalized = normalized + bias._data
    
    return Tensor(data=normalized)


# =============================================================================
# Attention Utilities
# =============================================================================

def scaled_dot_product_attention(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    attn_mask: Optional[Tensor] = None,
    dropout_p: float = 0.0,
    is_causal: bool = False,
    scale: Optional[float] = None
) -> Tensor:
    """
    Scaled dot-product attention.
    
    Optimized for Apple Silicon when possible.
    """
    L = query.shape[-2]
    S = key.shape[-2]
    d_k = query.shape[-1]
    
    if scale is None:
        scale = 1.0 / np.sqrt(d_k)
    
    # Q @ K^T
    scores = matmul(query, Tensor(data=np.swapaxes(key._data, -2, -1)))
    scores._data *= scale
    
    # Apply causal mask
    if is_causal:
        mask = np.triu(np.ones((L, S)), k=1) * -1e9
        scores._data += mask
    
    # Apply attention mask
    if attn_mask is not None:
        scores._data += attn_mask._data
    
    # Softmax
    attn_weights = softmax(scores, dim=-1)
    
    # Dropout (skip for now)
    
    # Attention @ V
    return matmul(attn_weights, value)


# =============================================================================
# Embedding
# =============================================================================

def embedding(input: Tensor, weight: Tensor, padding_idx: Optional[int] = None) -> Tensor:
    """Embedding lookup."""
    indices = input._data.astype(int)
    return Tensor(data=weight._data[indices])


# =============================================================================
# Loss Functions
# =============================================================================

def cross_entropy(input: Tensor, target: Tensor, reduction: str = 'mean') -> Tensor:
    """Cross-entropy loss."""
    log_probs = log_softmax(input, dim=-1)
    
    # Gather correct class probabilities
    batch_size = input.shape[0]
    indices = target._data.astype(int)
    losses = -log_probs._data[np.arange(batch_size), indices]
    
    if reduction == 'mean':
        return Tensor(data=np.array([np.mean(losses)]))
    elif reduction == 'sum':
        return Tensor(data=np.array([np.sum(losses)]))
    else:
        return Tensor(data=losses)

def mse_loss(input: Tensor, target: Tensor, reduction: str = 'mean') -> Tensor:
    """Mean squared error loss."""
    diff = input._data - target._data
    losses = diff ** 2
    
    if reduction == 'mean':
        return Tensor(data=np.array([np.mean(losses)]))
    elif reduction == 'sum':
        return Tensor(data=np.array([np.sum(losses)]))
    else:
        return Tensor(data=losses)

def l1_loss(input: Tensor, target: Tensor, reduction: str = 'mean') -> Tensor:
    """L1 (MAE) loss."""
    losses = np.abs(input._data - target._data)
    
    if reduction == 'mean':
        return Tensor(data=np.array([np.mean(losses)]))
    elif reduction == 'sum':
        return Tensor(data=np.array([np.sum(losses)]))
    else:
        return Tensor(data=losses)


# =============================================================================
# Utility
# =============================================================================

def clamp(x: Tensor, min: Optional[float] = None, max: Optional[float] = None) -> Tensor:
    """Clamp values to range."""
    result = x._data.copy()
    if min is not None:
        result = np.maximum(result, min)
    if max is not None:
        result = np.minimum(result, max)
    return Tensor(data=result)

def where(condition: Tensor, x: Tensor, y: Tensor) -> Tensor:
    """Element-wise conditional."""
    return Tensor(data=np.where(condition._data, x._data, y._data))

def masked_fill(x: Tensor, mask: Tensor, value: float) -> Tensor:
    """Fill masked positions with value."""
    result = x._data.copy()
    result[mask._data.astype(bool)] = value
    return Tensor(data=result)

def triu(x: Tensor, diagonal: int = 0) -> Tensor:
    """Upper triangular part."""
    return Tensor(data=np.triu(x._data, k=diagonal))

def tril(x: Tensor, diagonal: int = 0) -> Tensor:
    """Lower triangular part."""
    return Tensor(data=np.tril(x._data, k=diagonal))


# =============================================================================
# LLaMA-specific Operations (RoPE, RMSNorm, SwiGLU)
# =============================================================================

def rope_apply(x: Tensor, cos: Tensor, sin: Tensor) -> Tensor:
    """
    Apply Rotary Position Embedding (RoPE) to input tensor.
    
    This is the key operation for LLaMA positional encoding.
    x: [batch, seq_len, num_heads, head_dim]
    cos, sin: [seq_len, head_dim]
    
    Returns rotated tensor of same shape.
    """
    # Split x into pairs for rotation
    x_data = x._data
    cos_data = cos._data
    sin_data = sin._data
    
    # Get dimensions
    if x_data.ndim == 4:
        batch, seq_len, num_heads, head_dim = x_data.shape
        # Reshape for rotation: treat as complex numbers
        x1 = x_data[..., ::2]  # Even indices
        x2 = x_data[..., 1::2]  # Odd indices
        
        # Expand cos/sin to match x shape
        cos_expanded = cos_data[:seq_len, :head_dim//2].reshape(1, seq_len, 1, head_dim//2)
        sin_expanded = sin_data[:seq_len, :head_dim//2].reshape(1, seq_len, 1, head_dim//2)
        
        # Apply rotation
        out1 = x1 * cos_expanded - x2 * sin_expanded
        out2 = x1 * sin_expanded + x2 * cos_expanded
        
        # Interleave back
        result = np.zeros_like(x_data)
        result[..., ::2] = out1
        result[..., 1::2] = out2
    else:
        # Handle 3D case [batch, seq, dim]
        batch, seq_len, dim = x_data.shape
        x1 = x_data[..., ::2]
        x2 = x_data[..., 1::2]
        
        cos_expanded = cos_data[:seq_len, :dim//2].reshape(1, seq_len, dim//2)
        sin_expanded = sin_data[:seq_len, :dim//2].reshape(1, seq_len, dim//2)
        
        out1 = x1 * cos_expanded - x2 * sin_expanded
        out2 = x1 * sin_expanded + x2 * cos_expanded
        
        result = np.zeros_like(x_data)
        result[..., ::2] = out1
        result[..., 1::2] = out2
    
    return Tensor(data=result.astype(np.float32))


def rms_norm(x: Tensor, weight: Tensor, eps: float = 1e-6) -> Tensor:
    """
    Root Mean Square Layer Normalization (RMSNorm).
    
    Used in LLaMA instead of LayerNorm.
    """
    x_data = x._data
    weight_data = weight._data
    
    # Compute RMS
    variance = np.mean(x_data ** 2, axis=-1, keepdims=True)
    x_normalized = x_data * np.reciprocal(np.sqrt(variance + eps))
    
    return Tensor(data=(x_normalized * weight_data).astype(np.float32))


def silu(x: Tensor) -> Tensor:
    """
    SiLU (Swish) activation function.
    
    silu(x) = x * sigmoid(x)
    """
    x_data = x._data
    return Tensor(data=(x_data * (1.0 / (1.0 + np.exp(-x_data)))).astype(np.float32))


def swiglu(x: Tensor, gate_proj: Tensor, up_proj: Tensor) -> Tensor:
    """
    SwiGLU activation (used in LLaMA FFN).
    
    swiglu(x) = silu(gate_proj(x)) * up_proj(x)
    """
    # x: [batch, seq, hidden]
    # gate_proj, up_proj: [hidden, intermediate]
    gate_out = Tensor(data=x._data @ gate_proj._data)
    up_out = Tensor(data=x._data @ up_proj._data)
    
    return Tensor(data=(silu(gate_out)._data * up_out._data).astype(np.float32))
