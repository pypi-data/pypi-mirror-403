"""
Sapphire Llama Model - Complete LLM Implementation

Llama architecture implementation optimized for Apple Silicon.
Supports Llama 2, Llama 3, and compatible models (Mistral, etc.)

Copyright (c) 2026 SVECTOR. All rights reserved.
"""

from typing import Optional, Tuple, List
import numpy as np
from dataclasses import dataclass

from . import Tensor, tensor, zeros, ones
from .ops import (
    matmul, softmax, rms_norm, silu, rope_apply,
    scaled_dot_product_attention, embedding
)
from .nn import Module, Linear, Embedding, RMSNorm, ModuleList

# =============================================================================
# Llama Configuration
# =============================================================================

@dataclass
class LlamaConfig:
    """Llama model configuration."""
    hidden_size: int = 4096
    intermediate_size: int = 11008
    num_hidden_layers: int = 32
    num_attention_heads: int = 32
    num_key_value_heads: int = 32  # For GQA
    vocab_size: int = 32000
    max_position_embeddings: int = 4096
    rms_norm_eps: float = 1e-5
    rope_theta: float = 10000.0
    rope_scaling: Optional[dict] = None
    
    @classmethod
    def llama2_7b(cls) -> 'LlamaConfig':
        return cls(
            hidden_size=4096,
            intermediate_size=11008,
            num_hidden_layers=32,
            num_attention_heads=32,
            num_key_value_heads=32,
        )
    
    @classmethod
    def llama3_8b(cls) -> 'LlamaConfig':
        return cls(
            hidden_size=4096,
            intermediate_size=14336,
            num_hidden_layers=32,
            num_attention_heads=32,
            num_key_value_heads=8,
            vocab_size=128256,
            max_position_embeddings=8192,
            rope_theta=500000.0,
        )
    
    @classmethod
    def mistral_7b(cls) -> 'LlamaConfig':
        return cls(
            hidden_size=4096,
            intermediate_size=14336,
            num_hidden_layers=32,
            num_attention_heads=32,
            num_key_value_heads=8,
            vocab_size=32000,
            max_position_embeddings=32768,
            rope_theta=10000.0,
        )

# =============================================================================
# RoPE (Rotary Position Embedding)
# =============================================================================

class RotaryEmbedding(Module):
    """Rotary Position Embedding."""
    
    def __init__(self, dim: int, max_seq_len: int = 4096, theta: float = 10000.0):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.theta = theta
        
        # Precompute frequencies
        inv_freq = 1.0 / (theta ** (np.arange(0, dim, 2) / dim))
        t = np.arange(max_seq_len)
        freqs = np.outer(t, inv_freq)
        
        self.cos_cache = tensor(np.cos(freqs).astype(np.float32))
        self.sin_cache = tensor(np.sin(freqs).astype(np.float32))
    
    def forward(self, x: Tensor, positions: Optional[Tensor] = None) -> Tensor:
        seq_len = x.shape[1]
        
        if positions is None:
            cos = self.cos_cache._data[:seq_len]
            sin = self.sin_cache._data[:seq_len]
        else:
            pos = positions._data.astype(int)
            cos = self.cos_cache._data[pos]
            sin = self.sin_cache._data[pos]
        
        # Apply rotation
        x1 = x._data[..., ::2]
        x2 = x._data[..., 1::2]
        
        rotated = np.empty_like(x._data)
        rotated[..., ::2] = x1 * cos - x2 * sin
        rotated[..., 1::2] = x1 * sin + x2 * cos
        
        return tensor(rotated)

# =============================================================================
# Llama Attention
# =============================================================================

class LlamaAttention(Module):
    """Multi-head attention with GQA support."""
    
    def __init__(self, config: LlamaConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.num_kv_heads = config.num_key_value_heads
        self.head_dim = self.hidden_size // self.num_heads
        self.num_kv_groups = self.num_heads // self.num_kv_heads
        
        self.q_proj = Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
        self.k_proj = Linear(self.hidden_size, self.num_kv_heads * self.head_dim, bias=False)
        self.v_proj = Linear(self.hidden_size, self.num_kv_heads * self.head_dim, bias=False)
        self.o_proj = Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)
        
        self.rotary_emb = RotaryEmbedding(
            self.head_dim,
            max_seq_len=config.max_position_embeddings,
            theta=config.rope_theta
        )
    
    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Optional[Tensor] = None,
        position_ids: Optional[Tensor] = None,
        past_key_value: Optional[Tuple[Tensor, Tensor]] = None,
        use_cache: bool = False
    ) -> Tuple[Tensor, Optional[Tuple[Tensor, Tensor]]]:
        batch_size, seq_len, _ = hidden_states.shape
        
        # Project Q, K, V
        query = self.q_proj(hidden_states)
        key = self.k_proj(hidden_states)
        value = self.v_proj(hidden_states)
        
        # Reshape to (batch, num_heads, seq_len, head_dim)
        query = tensor(query._data.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3))
        key = tensor(key._data.reshape(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(0, 2, 1, 3))
        value = tensor(value._data.reshape(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(0, 2, 1, 3))
        
        # Apply RoPE
        query = self.rotary_emb(query, position_ids)
        key = self.rotary_emb(key, position_ids)
        
        # Handle KV cache
        if past_key_value is not None:
            past_key, past_value = past_key_value
            key = tensor(np.concatenate([past_key._data, key._data], axis=2))
            value = tensor(np.concatenate([past_value._data, value._data], axis=2))
        
        new_cache = (key, value) if use_cache else None
        
        # Repeat KV for GQA
        if self.num_kv_groups > 1:
            key = tensor(np.repeat(key._data, self.num_kv_groups, axis=1))
            value = tensor(np.repeat(value._data, self.num_kv_groups, axis=1))
        
        # Scaled dot-product attention
        attn_output = scaled_dot_product_attention(
            query, key, value,
            attn_mask=attention_mask,
            is_causal=(attention_mask is None and seq_len > 1)
        )
        
        # Reshape back
        attn_output = tensor(attn_output._data.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.hidden_size))
        
        # Output projection
        attn_output = self.o_proj(attn_output)
        
        return attn_output, new_cache

# =============================================================================
# Llama MLP
# =============================================================================

class LlamaMLP(Module):
    """Llama feed-forward network with SwiGLU."""
    
    def __init__(self, config: LlamaConfig):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size
        
        self.gate_proj = Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.up_proj = Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.down_proj = Linear(self.intermediate_size, self.hidden_size, bias=False)
    
    def forward(self, x: Tensor) -> Tensor:
        gate = silu(self.gate_proj(x))
        up = self.up_proj(x)
        return self.down_proj(tensor(gate._data * up._data))

# =============================================================================
# Llama Decoder Layer
# =============================================================================

class LlamaDecoderLayer(Module):
    """Single transformer decoder layer."""
    
    def __init__(self, config: LlamaConfig, layer_idx: int):
        super().__init__()
        self.hidden_size = config.hidden_size
        
        self.self_attn = LlamaAttention(config, layer_idx)
        self.mlp = LlamaMLP(config)
        self.input_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
    
    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Optional[Tensor] = None,
        position_ids: Optional[Tensor] = None,
        past_key_value: Optional[Tuple[Tensor, Tensor]] = None,
        use_cache: bool = False
    ) -> Tuple[Tensor, Optional[Tuple[Tensor, Tensor]]]:
        # Self-attention with residual
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states, present_kv = self.self_attn(
            hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            use_cache=use_cache
        )
        hidden_states = tensor(residual._data + hidden_states._data)
        
        # MLP with residual
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = tensor(residual._data + hidden_states._data)
        
        return hidden_states, present_kv

# =============================================================================
# Llama Model
# =============================================================================

class LlamaModel(Module):
    """Llama transformer model."""
    
    def __init__(self, config: LlamaConfig):
        super().__init__()
        self.config = config
        
        self.embed_tokens = Embedding(config.vocab_size, config.hidden_size)
        self.layers = ModuleList([
            LlamaDecoderLayer(config, i) for i in range(config.num_hidden_layers)
        ])
        self.norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
    
    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Optional[Tensor] = None,
        position_ids: Optional[Tensor] = None,
        past_key_values: Optional[List[Tuple[Tensor, Tensor]]] = None,
        use_cache: bool = False
    ) -> Tuple[Tensor, Optional[List[Tuple[Tensor, Tensor]]]]:
        batch_size, seq_len = input_ids.shape[:2]
        
        # Get embeddings
        hidden_states = self.embed_tokens(input_ids)
        
        # Create position IDs if not provided
        if position_ids is None:
            if past_key_values is not None and len(past_key_values) > 0:
                past_len = past_key_values[0][0].shape[2]
                position_ids = tensor(np.arange(past_len, past_len + seq_len)[None, :])
            else:
                position_ids = tensor(np.arange(seq_len)[None, :])
        
        # Initialize cache
        new_cache = [] if use_cache else None
        
        # Forward through layers
        for i, layer in enumerate(self.layers):
            past_kv = past_key_values[i] if past_key_values else None
            hidden_states, present_kv = layer(
                hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_value=past_kv,
                use_cache=use_cache
            )
            if use_cache:
                new_cache.append(present_kv)
        
        # Final norm
        hidden_states = self.norm(hidden_states)
        
        return hidden_states, new_cache

# =============================================================================
# Llama for Causal LM
# =============================================================================

class LlamaForCausalLM(Module):
    """Llama model with language modeling head."""
    
    def __init__(self, config: LlamaConfig):
        super().__init__()
        self.config = config
        self.model = LlamaModel(config)
        self.lm_head = Linear(config.hidden_size, config.vocab_size, bias=False)
    
    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Optional[Tensor] = None,
        position_ids: Optional[Tensor] = None,
        past_key_values: Optional[List[Tuple[Tensor, Tensor]]] = None,
        use_cache: bool = False
    ) -> Tuple[Tensor, Optional[List[Tuple[Tensor, Tensor]]]]:
        hidden_states, new_cache = self.model(
            input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            use_cache=use_cache
        )
        
        logits = self.lm_head(hidden_states)
        
        return logits, new_cache
    
    @classmethod
    def from_pretrained(cls, model_id: str, **kwargs) -> 'LlamaForCausalLM':
        """Load pretrained model."""
        from .loader import load_model, ModelConfig, WeightConverter
        
        # Get config
        hf_config = ModelConfig.from_pretrained(model_id)
        config = LlamaConfig(
            hidden_size=hf_config.hidden_size,
            intermediate_size=hf_config.intermediate_size,
            num_hidden_layers=hf_config.num_hidden_layers,
            num_attention_heads=hf_config.num_attention_heads,
            num_key_value_heads=hf_config.num_key_value_heads,
            vocab_size=hf_config.vocab_size,
            max_position_embeddings=hf_config.max_position_embeddings,
            rms_norm_eps=hf_config.rms_norm_eps,
            rope_theta=hf_config.rope_theta,
        )
        
        # Create model
        model = cls(config)
        
        # Load weights
        weights = load_model(model_id, **kwargs)
        weights = WeightConverter.convert(weights)
        
        # Load state dict (simplified)
        for name, param in model.named_parameters():
            if name in weights:
                param._data[:] = weights[name]._data
        
        return model
    
    def generate(
        self,
        input_ids: Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 0.9,
        top_k: int = 50
    ) -> Tensor:
        """Generate text autoregressively."""
        generated = input_ids._data.copy()
        past_key_values = None
        
        for _ in range(max_new_tokens):
            # Forward pass
            if past_key_values is None:
                curr_input = tensor(generated)
            else:
                curr_input = tensor(generated[:, -1:])
            
            logits, past_key_values = self.forward(
                curr_input,
                past_key_values=past_key_values,
                use_cache=True
            )
            
            # Get next token logits
            next_logits = logits._data[:, -1, :] / temperature
            
            # Top-k filtering
            if top_k > 0:
                indices = np.argsort(next_logits, axis=-1)[..., :-top_k]
                np.put_along_axis(next_logits, indices, -float('inf'), axis=-1)
            
            # Top-p (nucleus) filtering
            if top_p < 1.0:
                sorted_logits = np.sort(next_logits, axis=-1)[:, ::-1]
                sorted_probs = np.exp(sorted_logits - np.max(sorted_logits, axis=-1, keepdims=True))
                sorted_probs /= sorted_probs.sum(axis=-1, keepdims=True)
                cumsum = np.cumsum(sorted_probs, axis=-1)
                mask = cumsum > top_p
                mask[:, 1:] = mask[:, :-1].copy()
                mask[:, 0] = False
                sorted_logits[mask] = -float('inf')
            
            # Sample
            probs = np.exp(next_logits - np.max(next_logits, axis=-1, keepdims=True))
            probs /= probs.sum(axis=-1, keepdims=True)
            next_token = np.array([[np.random.choice(probs.shape[-1], p=probs[0])]])
            
            # Append
            generated = np.concatenate([generated, next_token], axis=-1)
            
            # Check for EOS
            if next_token[0, 0] == 2:  # EOS token
                break
        
        return tensor(generated)
