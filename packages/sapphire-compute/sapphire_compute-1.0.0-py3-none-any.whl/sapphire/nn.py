"""
Sapphire Neural Network Modules

PyTorch-compatible neural network layers that run on Apple Silicon
with AMX acceleration.

Copyright (c) 2026 SVECTOR. All rights reserved.
"""

import math
from typing import Callable, List, Optional, Tuple, Union

import numpy as np

from . import Tensor, ones, randn, tensor, zeros
from .ops import (cross_entropy, embedding, gelu, layer_norm, matmul, relu,
                  rms_norm, scaled_dot_product_attention, silu, softmax)

# =============================================================================
# Base Module
# =============================================================================

class Module:
    """Base class for all neural network modules."""
    
    def __init__(self):
        self._parameters: dict = {}
        self._modules: dict = {}
        self._training: bool = True
    
    def forward(self, *args, **kwargs):
        raise NotImplementedError
    
    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
    
    def parameters(self) -> List[Tensor]:
        """Return all parameters."""
        params = list(self._parameters.values())
        for module in self._modules.values():
            params.extend(module.parameters())
        return params
    
    def named_parameters(self) -> List[Tuple[str, Tensor]]:
        """Return all named parameters."""
        params = [(name, param) for name, param in self._parameters.items()]
        for name, module in self._modules.items():
            for param_name, param in module.named_parameters():
                params.append((f"{name}.{param_name}", param))
        return params
    
    def train(self, mode: bool = True) -> 'Module':
        """Set training mode."""
        self._training = mode
        for module in self._modules.values():
            module.train(mode)
        return self
    
    def eval(self) -> 'Module':
        """Set evaluation mode."""
        return self.train(False)
    
    def __setattr__(self, name: str, value):
        if isinstance(value, Module):
            self._modules[name] = value
        elif isinstance(value, Parameter):
            self._parameters[name] = value.data
        super().__setattr__(name, value)
    
    def state_dict(self) -> dict:
        """Return state dictionary."""
        state = {}
        for name, param in self.named_parameters():
            state[name] = param._data.copy()
        return state
    
    def load_state_dict(self, state_dict: dict):
        """Load state dictionary."""
        for name, param in self.named_parameters():
            if name in state_dict:
                param._data[:] = state_dict[name]


class Parameter:
    """Wrapper for learnable parameters."""
    
    def __init__(self, data: Tensor, requires_grad: bool = True):
        self.data = data
        self.data._requires_grad = requires_grad


# =============================================================================
# Linear Layers
# =============================================================================

class Linear(Module):
    """Linear (fully connected) layer."""
    
    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        # Initialize weights (Kaiming initialization)
        std = 1.0 / math.sqrt(in_features)
        self.weight = Parameter(tensor(
            np.random.uniform(-std, std, (out_features, in_features)).astype(np.float32)
        ))
        
        if bias:
            self.bias = Parameter(zeros(out_features))
        else:
            self.bias = None
    
    def forward(self, x: Tensor) -> Tensor:
        # x: (*, in_features)
        # weight: (out_features, in_features)
        # output: (*, out_features)
        
        # Reshape for matmul
        orig_shape = x.shape
        x_2d = tensor(x._data.reshape(-1, self.in_features))
        
        # Weight transpose for correct matmul
        weight_t = tensor(self.weight.data._data.T)
        out = matmul(x_2d, weight_t)
        
        if self.bias is not None:
            out._data += self.bias.data._data
        
        # Reshape back
        new_shape = orig_shape[:-1] + (self.out_features,)
        return tensor(out._data.reshape(new_shape))


# =============================================================================
# Embedding Layers
# =============================================================================

class Embedding(Module):
    """Embedding layer."""
    
    def __init__(self, num_embeddings: int, embedding_dim: int, padding_idx: Optional[int] = None):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        
        self.weight = Parameter(randn(num_embeddings, embedding_dim))
        
        if padding_idx is not None:
            self.weight.data._data[padding_idx] = 0
    
    def forward(self, input: Tensor) -> Tensor:
        return embedding(input, self.weight.data, self.padding_idx)


# =============================================================================
# Normalization Layers
# =============================================================================

class LayerNorm(Module):
    """Layer normalization."""
    
    def __init__(self, normalized_shape: Union[int, Tuple[int, ...]], eps: float = 1e-5):
        super().__init__()
        if isinstance(normalized_shape, int):
            normalized_shape = (normalized_shape,)
        self.normalized_shape = normalized_shape
        self.eps = eps
        
        self.weight = Parameter(ones(*normalized_shape))
        self.bias = Parameter(zeros(*normalized_shape))
    
    def forward(self, x: Tensor) -> Tensor:
        return layer_norm(x, self.normalized_shape, self.weight.data, self.bias.data, self.eps)


class RMSNorm(Module):
    """RMS normalization (used in Llama)."""
    
    def __init__(self, hidden_size: int, eps: float = 1e-5):
        super().__init__()
        self.hidden_size = hidden_size
        self.eps = eps
        self.weight = Parameter(ones(hidden_size))
    
    def forward(self, x: Tensor) -> Tensor:
        return rms_norm(x, self.weight.data, self.eps)


# =============================================================================
# Activation Modules
# =============================================================================

class ReLU(Module):
    def forward(self, x: Tensor) -> Tensor:
        return relu(x)

class GELU(Module):
    def __init__(self, approximate: str = 'tanh'):
        super().__init__()
        self.approximate = approximate
    
    def forward(self, x: Tensor) -> Tensor:
        return gelu(x, self.approximate)

class SiLU(Module):
    def forward(self, x: Tensor) -> Tensor:
        return silu(x)

class Softmax(Module):
    def __init__(self, dim: int = -1):
        super().__init__()
        self.dim = dim
    
    def forward(self, x: Tensor) -> Tensor:
        return softmax(x, self.dim)


# =============================================================================
# Attention
# =============================================================================

class MultiHeadAttention(Module):
    """Multi-head attention."""
    
    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        dropout: float = 0.0,
        bias: bool = True,
        add_bias_kv: bool = False,
        kdim: Optional[int] = None,
        vdim: Optional[int] = None
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.dropout = dropout
        
        assert self.head_dim * num_heads == embed_dim, "embed_dim must be divisible by num_heads"
        
        kdim = kdim or embed_dim
        vdim = vdim or embed_dim
        
        self.q_proj = Linear(embed_dim, embed_dim, bias=bias)
        self.k_proj = Linear(kdim, embed_dim, bias=bias)
        self.v_proj = Linear(vdim, embed_dim, bias=bias)
        self.out_proj = Linear(embed_dim, embed_dim, bias=bias)
    
    def forward(
        self,
        query: Tensor,
        key: Tensor,
        value: Tensor,
        attn_mask: Optional[Tensor] = None,
        is_causal: bool = False
    ) -> Tuple[Tensor, Optional[Tensor]]:
        batch_size = query.shape[0]
        seq_len = query.shape[1]
        
        # Project
        q = self.q_proj(query)
        k = self.k_proj(key)
        v = self.v_proj(value)
        
        # Reshape to (batch, num_heads, seq_len, head_dim)
        q = tensor(q._data.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3))
        k = tensor(k._data.reshape(batch_size, -1, self.num_heads, self.head_dim).transpose(0, 2, 1, 3))
        v = tensor(v._data.reshape(batch_size, -1, self.num_heads, self.head_dim).transpose(0, 2, 1, 3))
        
        # Attention
        attn_output = scaled_dot_product_attention(
            q, k, v,
            attn_mask=attn_mask,
            dropout_p=self.dropout if self._training else 0.0,
            is_causal=is_causal
        )
        
        # Reshape back
        attn_output = tensor(attn_output._data.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.embed_dim))
        
        # Output projection
        output = self.out_proj(attn_output)
        
        return output, None


# =============================================================================
# Transformer Components
# =============================================================================

class TransformerEncoderLayer(Module):
    """Transformer encoder layer."""
    
    def __init__(
        self,
        d_model: int,
        nhead: int,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        activation: str = 'gelu',
        norm_first: bool = True
    ):
        super().__init__()
        self.norm_first = norm_first
        
        self.self_attn = MultiHeadAttention(d_model, nhead, dropout=dropout)
        
        self.linear1 = Linear(d_model, dim_feedforward)
        self.linear2 = Linear(dim_feedforward, d_model)
        
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)
        
        self.activation = GELU() if activation == 'gelu' else ReLU()
    
    def forward(self, src: Tensor, src_mask: Optional[Tensor] = None) -> Tensor:
        if self.norm_first:
            # Pre-norm
            x = src
            x = x + self._sa_block(self.norm1(x), src_mask)
            x = x + self._ff_block(self.norm2(x))
        else:
            # Post-norm
            x = self.norm1(src + self._sa_block(src, src_mask))
            x = self.norm2(x + self._ff_block(x))
        return x
    
    def _sa_block(self, x: Tensor, attn_mask: Optional[Tensor]) -> Tensor:
        x, _ = self.self_attn(x, x, x, attn_mask=attn_mask)
        return x
    
    def _ff_block(self, x: Tensor) -> Tensor:
        x = self.linear1(x)
        x = self.activation(x)
        x = self.linear2(x)
        return x


# =============================================================================
# Loss Functions as Modules
# =============================================================================

class CrossEntropyLoss(Module):
    """Cross-entropy loss."""
    
    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        self.reduction = reduction
    
    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        return cross_entropy(input, target, reduction=self.reduction)


# =============================================================================
# Container Modules
# =============================================================================

class Sequential(Module):
    """Sequential container."""
    
    def __init__(self, *modules):
        super().__init__()
        for i, module in enumerate(modules):
            self._modules[str(i)] = module
    
    def forward(self, x: Tensor) -> Tensor:
        for module in self._modules.values():
            x = module(x)
        return x


class ModuleList(Module):
    """List of modules."""
    
    def __init__(self, modules: Optional[List[Module]] = None):
        super().__init__()
        if modules is not None:
            for i, module in enumerate(modules):
                self._modules[str(i)] = module
    
    def append(self, module: Module):
        self._modules[str(len(self._modules))] = module
    
    def __len__(self):
        return len(self._modules)
    
    def __iter__(self):
        return iter(self._modules.values())
    
    def __getitem__(self, idx: int):
        return list(self._modules.values())[idx]


# =============================================================================
# Dropout (No-op for inference)
# =============================================================================

class Dropout(Module):
    """Dropout layer (no-op during inference)."""
    
    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = p
    
    def forward(self, x: Tensor) -> Tensor:
        if not self._training or self.p == 0:
            return x
        
        mask = np.random.binomial(1, 1 - self.p, size=x.shape).astype(np.float32)
        return tensor(x._data * mask / (1 - self.p))


# =============================================================================
# Convolutional Layers - cuDNN REPLACEMENT
# =============================================================================

class Conv2d(Module):
    """2D Convolution - Complete cuDNN replacement."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = 1,
        padding: Union[int, Tuple[int, int]] = 0,
        dilation: Union[int, Tuple[int, int]] = 1,
        groups: int = 1,
        bias: bool = True
    ):
        super().__init__()
        
        if isinstance(kernel_size, int):
            kernel_size = (kernel_size, kernel_size)
        if isinstance(stride, int):
            stride = (stride, stride)
        if isinstance(padding, int):
            padding = (padding, padding)
        if isinstance(dilation, int):
            dilation = (dilation, dilation)
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.groups = groups
        
        # Kaiming initialization
        k = groups / (in_channels * kernel_size[0] * kernel_size[1])
        std = math.sqrt(k)
        
        self.weight = Parameter(tensor(
            np.random.uniform(-std, std, 
                (out_channels, in_channels // groups, kernel_size[0], kernel_size[1])
            ).astype(np.float32)
        ))
        
        if bias:
            self.bias = Parameter(zeros(out_channels))
        else:
            self.bias = None
    
    def forward(self, x: Tensor) -> Tensor:
        from .native import is_native_available, native_conv2d
        
        if is_native_available():
            bias_data = self.bias.data._data if self.bias is not None else None
            result = native_conv2d(
                x._data, self.weight.data._data, bias_data,
                self.stride, self.padding, self.dilation, self.groups
            )
            return tensor(result)
        
        # Fallback - use numpy
        raise NotImplementedError("Conv2d requires native library")


class BatchNorm2d(Module):
    """2D Batch Normalization - cuDNN replacement."""
    
    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        momentum: float = 0.1,
        affine: bool = True,
        track_running_stats: bool = True
    ):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats
        
        if affine:
            self.weight = Parameter(ones(num_features))
            self.bias = Parameter(zeros(num_features))
        else:
            self.weight = None
            self.bias = None
        
        if track_running_stats:
            self.running_mean = zeros(num_features)
            self.running_var = ones(num_features)
            self.num_batches_tracked = 0
        else:
            self.running_mean = None
            self.running_var = None
    
    def forward(self, x: Tensor) -> Tensor:
        from .native import is_native_available, native_batchnorm
        
        if is_native_available():
            gamma = self.weight.data._data if self.weight is not None else np.ones(self.num_features, dtype=np.float32)
            beta = self.bias.data._data if self.bias is not None else np.zeros(self.num_features, dtype=np.float32)
            
            result, save_mean, save_invstd = native_batchnorm(
                x._data, gamma, beta,
                self.running_mean._data, self.running_var._data,
                self._training, self.momentum, self.eps
            )
            return tensor(result)
        
        # Fallback
        mean = np.mean(x._data, axis=(0, 2, 3), keepdims=True)
        var = np.var(x._data, axis=(0, 2, 3), keepdims=True)
        x_norm = (x._data - mean) / np.sqrt(var + self.eps)
        
        if self.affine:
            gamma = self.weight.data._data.reshape(1, -1, 1, 1)
            beta = self.bias.data._data.reshape(1, -1, 1, 1)
            x_norm = x_norm * gamma + beta
        
        return tensor(x_norm)


class MaxPool2d(Module):
    """2D Max Pooling - cuDNN replacement."""
    
    def __init__(
        self,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = None,
        padding: Union[int, Tuple[int, int]] = 0
    ):
        super().__init__()
        
        if isinstance(kernel_size, int):
            kernel_size = (kernel_size, kernel_size)
        if stride is None:
            stride = kernel_size
        elif isinstance(stride, int):
            stride = (stride, stride)
        if isinstance(padding, int):
            padding = (padding, padding)
        
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
    
    def forward(self, x: Tensor) -> Tensor:
        from .native import is_native_available, native_maxpool2d
        
        if is_native_available():
            result, _ = native_maxpool2d(x._data, self.kernel_size, self.stride, self.padding)
            return tensor(result)
        
        # Fallback
        N, C, H, W = x.shape
        kH, kW = self.kernel_size
        sH, sW = self.stride
        pH, pW = self.padding
        
        oH = (H + 2 * pH - kH) // sH + 1
        oW = (W + 2 * pW - kW) // sW + 1
        
        # Pad
        if pH > 0 or pW > 0:
            padded = np.pad(x._data, ((0, 0), (0, 0), (pH, pH), (pW, pW)), 
                          mode='constant', constant_values=float('-inf'))
        else:
            padded = x._data
        
        output = np.zeros((N, C, oH, oW), dtype=np.float32)
        
        for i in range(oH):
            for j in range(oW):
                h_start = i * sH
                w_start = j * sW
                output[:, :, i, j] = np.max(
                    padded[:, :, h_start:h_start+kH, w_start:w_start+kW],
                    axis=(2, 3)
                )
        
        return tensor(output)


class AvgPool2d(Module):
    """2D Average Pooling."""
    
    def __init__(
        self,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = None,
        padding: Union[int, Tuple[int, int]] = 0
    ):
        super().__init__()
        
        if isinstance(kernel_size, int):
            kernel_size = (kernel_size, kernel_size)
        if stride is None:
            stride = kernel_size
        elif isinstance(stride, int):
            stride = (stride, stride)
        if isinstance(padding, int):
            padding = (padding, padding)
        
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
    
    def forward(self, x: Tensor) -> Tensor:
        from .native import is_native_available, native_avgpool2d
        
        if is_native_available():
            result = native_avgpool2d(x._data, self.kernel_size, self.stride, self.padding)
            return tensor(result)
        
        # Fallback
        N, C, H, W = x.shape
        kH, kW = self.kernel_size
        sH, sW = self.stride
        pH, pW = self.padding
        
        oH = (H + 2 * pH - kH) // sH + 1
        oW = (W + 2 * pW - kW) // sW + 1
        
        if pH > 0 or pW > 0:
            padded = np.pad(x._data, ((0, 0), (0, 0), (pH, pH), (pW, pW)), mode='constant')
        else:
            padded = x._data
        
        output = np.zeros((N, C, oH, oW), dtype=np.float32)
        
        for i in range(oH):
            for j in range(oW):
                h_start = i * sH
                w_start = j * sW
                output[:, :, i, j] = np.mean(
                    padded[:, :, h_start:h_start+kH, w_start:w_start+kW],
                    axis=(2, 3)
                )
        
        return tensor(output)


class AdaptiveAvgPool2d(Module):
    """Adaptive Average Pooling - outputs fixed size regardless of input."""
    
    def __init__(self, output_size: Union[int, Tuple[int, int]]):
        super().__init__()
        if isinstance(output_size, int):
            output_size = (output_size, output_size)
        self.output_size = output_size
    
    def forward(self, x: Tensor) -> Tensor:
        N, C, H, W = x.shape
        oH, oW = self.output_size
        
        output = np.zeros((N, C, oH, oW), dtype=np.float32)
        
        for i in range(oH):
            h_start = int(i * H / oH)
            h_end = int((i + 1) * H / oH)
            for j in range(oW):
                w_start = int(j * W / oW)
                w_end = int((j + 1) * W / oW)
                output[:, :, i, j] = np.mean(
                    x._data[:, :, h_start:h_end, w_start:w_end],
                    axis=(2, 3)
                )
        
        return tensor(output)


class Flatten(Module):
    """Flatten layer."""
    
    def __init__(self, start_dim: int = 1, end_dim: int = -1):
        super().__init__()
        self.start_dim = start_dim
        self.end_dim = end_dim
    
    def forward(self, x: Tensor) -> Tensor:
        shape = x.shape
        end_dim = self.end_dim if self.end_dim >= 0 else len(shape) + self.end_dim
        
        new_shape = shape[:self.start_dim] + (-1,) + shape[end_dim+1:]
        return tensor(x._data.reshape(new_shape))


# =============================================================================
# Export commonly used classes
# =============================================================================

__all__ = [
    'Module', 'Parameter', 'Linear', 'Embedding',
    'LayerNorm', 'RMSNorm',
    'ReLU', 'GELU', 'SiLU', 'Softmax',
    'MultiHeadAttention', 'TransformerEncoderLayer',
    'CrossEntropyLoss',
    'Sequential', 'ModuleList', 'Dropout',
    # cuDNN replacements
    'Conv2d', 'BatchNorm2d', 'MaxPool2d', 'AvgPool2d', 'AdaptiveAvgPool2d',
    'Flatten'
]
