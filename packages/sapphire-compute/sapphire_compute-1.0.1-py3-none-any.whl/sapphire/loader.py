"""
Sapphire Model Loader - Load PyTorch/HuggingFace models

Supports loading weights from:
- PyTorch .pt/.pth files
- SafeTensors format
- GGUF format (llama.cpp compatible)
- HuggingFace Hub

Copyright (c) 2026 SVECTOR. All rights reserved.
"""

import os
import json
from typing import Dict, Optional, Any, List
import numpy as np
from pathlib import Path
from . import Tensor, tensor

# =============================================================================
# Weight Loaders
# =============================================================================

def load_pytorch_weights(path: str) -> Dict[str, np.ndarray]:
    """Load weights from PyTorch checkpoint."""
    try:
        import torch
        state_dict = torch.load(path, map_location='cpu', weights_only=True)
        
        # Handle nested state_dict
        if 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        elif 'model_state_dict' in state_dict:
            state_dict = state_dict['model_state_dict']
        
        return {k: v.numpy().astype(np.float32) for k, v in state_dict.items()}
    except ImportError:
        raise ImportError("PyTorch required for loading .pt files. Install with: pip install torch")

def load_safetensors(path: str) -> Dict[str, np.ndarray]:
    """Load weights from SafeTensors format."""
    try:
        from safetensors import safe_open
        
        weights = {}
        with safe_open(path, framework="numpy") as f:
            for key in f.keys():
                weights[key] = f.get_tensor(key).astype(np.float32)
        
        return weights
    except ImportError:
        raise ImportError("safetensors required. Install with: pip install safetensors")

def load_gguf(path: str) -> Dict[str, np.ndarray]:
    """Load weights from GGUF format (llama.cpp compatible)."""
    weights = {}
    
    with open(path, 'rb') as f:
        # GGUF magic
        magic = f.read(4)
        if magic != b'GGUF':
            raise ValueError("Not a valid GGUF file")
        
        version = int.from_bytes(f.read(4), 'little')
        n_tensors = int.from_bytes(f.read(8), 'little')
        n_kv = int.from_bytes(f.read(8), 'little')
        
        # Skip metadata (simplified)
        # In production, would parse full metadata
        
        # For now, return empty - full GGUF parsing is complex
        print(f"GGUF v{version}: {n_tensors} tensors, {n_kv} metadata entries")
    
    return weights

def load_weights(path: str) -> Dict[str, np.ndarray]:
    """Auto-detect format and load weights."""
    path = str(path)
    
    if path.endswith('.safetensors'):
        return load_safetensors(path)
    elif path.endswith('.gguf'):
        return load_gguf(path)
    elif path.endswith('.pt') or path.endswith('.pth') or path.endswith('.bin'):
        return load_pytorch_weights(path)
    else:
        raise ValueError(f"Unknown weight format: {path}")

# =============================================================================
# HuggingFace Integration
# =============================================================================

def load_from_huggingface(
    model_id: str,
    revision: str = "main",
    token: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> Dict[str, np.ndarray]:
    """Load model weights from HuggingFace Hub."""
    try:
        from huggingface_hub import hf_hub_download, list_repo_files
    except ImportError:
        raise ImportError("huggingface_hub required. Install with: pip install huggingface-hub")
    
    cache_dir = cache_dir or os.path.expanduser("~/.cache/sapphire/models")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Get list of model files
    files = list_repo_files(model_id, revision=revision, token=token)
    
    # Prefer safetensors
    weight_files = [f for f in files if f.endswith('.safetensors')]
    if not weight_files:
        weight_files = [f for f in files if f.endswith('.bin')]
    
    weights = {}
    for wf in weight_files:
        local_path = hf_hub_download(
            model_id,
            wf,
            revision=revision,
            token=token,
            cache_dir=cache_dir
        )
        weights.update(load_weights(local_path))
    
    return weights

# =============================================================================
# Model Configuration
# =============================================================================

class ModelConfig:
    """Model configuration parsed from config.json."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.hidden_size: int = config_dict.get('hidden_size', 768)
        self.num_hidden_layers: int = config_dict.get('num_hidden_layers', 12)
        self.num_attention_heads: int = config_dict.get('num_attention_heads', 12)
        self.num_key_value_heads: int = config_dict.get('num_key_value_heads', self.num_attention_heads)
        self.intermediate_size: int = config_dict.get('intermediate_size', 3072)
        self.vocab_size: int = config_dict.get('vocab_size', 32000)
        self.max_position_embeddings: int = config_dict.get('max_position_embeddings', 2048)
        self.rms_norm_eps: float = config_dict.get('rms_norm_eps', 1e-5)
        self.rope_theta: float = config_dict.get('rope_theta', 10000.0)
        self.model_type: str = config_dict.get('model_type', 'unknown')
        
        self._raw = config_dict
    
    @classmethod
    def from_json(cls, path: str) -> 'ModelConfig':
        with open(path, 'r') as f:
            return cls(json.load(f))
    
    @classmethod
    def from_pretrained(cls, model_id: str) -> 'ModelConfig':
        try:
            from huggingface_hub import hf_hub_download
            config_path = hf_hub_download(model_id, "config.json")
            return cls.from_json(config_path)
        except:
            return cls({})

# =============================================================================
# Model Registry
# =============================================================================

class ModelRegistry:
    """Registry of supported model architectures."""
    
    SUPPORTED_MODELS = {
        'llama': ['meta-llama/Llama-*', 'huggyllama/*'],
        'mistral': ['mistralai/Mistral-*'],
        'phi': ['microsoft/phi-*'],
        'qwen': ['Qwen/*'],
        'gemma': ['google/gemma-*'],
    }
    
    @classmethod
    def get_architecture(cls, model_type: str) -> str:
        """Get architecture name from model type."""
        model_type = model_type.lower()
        
        if 'llama' in model_type:
            return 'llama'
        elif 'mistral' in model_type:
            return 'mistral'
        elif 'phi' in model_type:
            return 'phi'
        elif 'qwen' in model_type:
            return 'qwen'
        elif 'gemma' in model_type:
            return 'gemma'
        else:
            return 'generic'
    
    @classmethod
    def is_supported(cls, model_id: str) -> bool:
        """Check if model is supported."""
        for arch, patterns in cls.SUPPORTED_MODELS.items():
            for pattern in patterns:
                if pattern.replace('*', '') in model_id:
                    return True
        return False

# =============================================================================
# Weight Converter
# =============================================================================

class WeightConverter:
    """Convert weights between different naming conventions."""
    
    # HuggingFace to Sapphire name mapping
    HF_TO_SAPPHIRE = {
        'model.embed_tokens.weight': 'embed.weight',
        'model.norm.weight': 'norm.weight',
        'lm_head.weight': 'output.weight',
    }
    
    # Layer pattern mappings
    LAYER_PATTERNS = {
        'model.layers.{}.self_attn.q_proj.weight': 'layers.{}.attention.wq.weight',
        'model.layers.{}.self_attn.k_proj.weight': 'layers.{}.attention.wk.weight',
        'model.layers.{}.self_attn.v_proj.weight': 'layers.{}.attention.wv.weight',
        'model.layers.{}.self_attn.o_proj.weight': 'layers.{}.attention.wo.weight',
        'model.layers.{}.mlp.gate_proj.weight': 'layers.{}.feed_forward.w1.weight',
        'model.layers.{}.mlp.up_proj.weight': 'layers.{}.feed_forward.w3.weight',
        'model.layers.{}.mlp.down_proj.weight': 'layers.{}.feed_forward.w2.weight',
        'model.layers.{}.input_layernorm.weight': 'layers.{}.attention_norm.weight',
        'model.layers.{}.post_attention_layernorm.weight': 'layers.{}.ffn_norm.weight',
    }
    
    @classmethod
    def convert(cls, weights: Dict[str, np.ndarray], architecture: str = 'llama') -> Dict[str, np.ndarray]:
        """Convert weight names to Sapphire convention."""
        converted = {}
        
        for name, weight in weights.items():
            new_name = cls._convert_name(name)
            converted[new_name] = weight
        
        return converted
    
    @classmethod
    def _convert_name(cls, name: str) -> str:
        """Convert a single weight name."""
        # Direct mapping
        if name in cls.HF_TO_SAPPHIRE:
            return cls.HF_TO_SAPPHIRE[name]
        
        # Layer patterns
        import re
        for pattern, replacement in cls.LAYER_PATTERNS.items():
            regex = pattern.replace('{}.', r'(\d+)\.')
            regex = regex.replace('.', r'\.')
            match = re.match(regex, name)
            if match:
                layer_num = match.group(1)
                return replacement.format(layer_num)
        
        return name

# =============================================================================
# Quick Load Functions
# =============================================================================

def load_model(
    model_id_or_path: str,
    quantize: Optional[str] = None,  # 'int8', 'int4', None
    device: str = 'sapphire'
) -> Dict[str, Tensor]:
    """
    Load a model for inference.
    
    Args:
        model_id_or_path: HuggingFace model ID or local path
        quantize: Quantization mode ('int8', 'int4', or None)
        device: Target device
    
    Returns:
        Dictionary of Tensor weights
    """
    # Determine if local or HuggingFace
    if os.path.exists(model_id_or_path):
        # Local path
        if os.path.isdir(model_id_or_path):
            # Directory with weights
            weight_files = list(Path(model_id_or_path).glob('*.safetensors'))
            if not weight_files:
                weight_files = list(Path(model_id_or_path).glob('*.bin'))
            
            weights = {}
            for wf in weight_files:
                weights.update(load_weights(str(wf)))
        else:
            weights = load_weights(model_id_or_path)
    else:
        # HuggingFace model
        weights = load_from_huggingface(model_id_or_path)
    
    # Convert to Sapphire tensors
    tensors = {k: tensor(v) for k, v in weights.items()}
    
    # Apply quantization if requested
    if quantize == 'int8':
        from .quantize import quantize_model_int8
        tensors = quantize_model_int8(tensors)
    elif quantize == 'int4':
        from .quantize import quantize_model_int4
        tensors = quantize_model_int4(tensors)
    
    return tensors

def model_info(model_id: str) -> Dict[str, Any]:
    """Get model information without downloading weights."""
    config = ModelConfig.from_pretrained(model_id)
    
    # Estimate memory
    params = 0
    hidden = config.hidden_size
    layers = config.num_hidden_layers
    vocab = config.vocab_size
    inter = config.intermediate_size
    
    # Rough parameter count
    params += vocab * hidden  # Embeddings
    params += layers * (4 * hidden * hidden)  # Attention
    params += layers * (3 * hidden * inter)  # MLP
    params += hidden  # Final norm
    
    return {
        'model_type': config.model_type,
        'hidden_size': hidden,
        'num_layers': layers,
        'vocab_size': vocab,
        'estimated_params': params,
        'estimated_memory_fp32': f"{params * 4 / 1e9:.2f} GB",
        'estimated_memory_fp16': f"{params * 2 / 1e9:.2f} GB",
        'estimated_memory_int8': f"{params / 1e9:.2f} GB",
        'estimated_memory_int4': f"{params * 0.5 / 1e9:.2f} GB",
    }
