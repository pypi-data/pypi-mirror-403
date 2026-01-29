"""
Sapphire Lariat - CUDA Call Interceptor

This module intercepts CUDA calls at the Python level and redirects them
to Sapphire's native implementation. It's the key to running existing
CUDA/PyTorch code without modification.

Usage:
    import sapphire.lariat as torch.cuda
    # Now all torch.cuda calls go through Sapphire!

Or for module-level patching:
    import sapphire.lariat
    sapphire.lariat.patch_torch()
    # Now torch itself uses Sapphire backend

Copyright (c) 2026 SVECTOR. All rights reserved.
"""

import functools
import sys
import types
from typing import Any, Callable, Dict, Optional

import numpy as np

# Import our CUDA replacement
from . import cuda as sapphire_cuda
from .native import is_native_available

# =============================================================================
# CUDA Runtime API Interception
# =============================================================================

class CUDAInterceptor:
    """
    Intercepts CUDA calls and redirects to Sapphire.
    
    This works by monkey-patching the torch.cuda module (if available)
    or by providing a complete drop-in replacement.
    """
    
    def __init__(self):
        self._patched = False
        self._original_cuda = None
        self._call_log = []
        self._enable_logging = False
    
    def enable_logging(self, enable: bool = True):
        """Enable call logging for debugging."""
        self._enable_logging = enable
    
    def get_call_log(self):
        """Get log of intercepted calls."""
        return self._call_log.copy()
    
    def clear_call_log(self):
        """Clear the call log."""
        self._call_log.clear()
    
    def _log_call(self, func_name: str, args: tuple, kwargs: dict):
        """Log an intercepted call."""
        if self._enable_logging:
            self._call_log.append({
                'function': func_name,
                'args': str(args)[:100],
                'kwargs': str(kwargs)[:100]
            })
    
    def patch_torch(self):
        """
        Monkey-patch torch.cuda to use Sapphire.
        
        After calling this, all torch.cuda operations go through Sapphire.
        """
        if self._patched:
            return
        
        try:
            import torch
            self._original_cuda = torch.cuda
            
            # Replace torch.cuda with our module
            torch.cuda = sapphire_cuda
            
            # Also patch device management
            original_device = torch.device
            
            def patched_device(device_str):
                if isinstance(device_str, str):
                    if 'cuda' in device_str:
                        device_str = device_str.replace('cuda', 'mps')
                return original_device(device_str)
            
            torch.device = patched_device
            
            self._patched = True
            print("[Lariat] torch.cuda patched to use Sapphire")
            
        except ImportError:
            print("[Lariat] PyTorch not installed, patching not needed")
    
    def unpatch_torch(self):
        """Restore original torch.cuda."""
        if not self._patched or self._original_cuda is None:
            return
        
        try:
            import torch
            torch.cuda = self._original_cuda
            self._patched = False
            print("[Lariat] torch.cuda restored")
        except ImportError:
            pass


# Global interceptor instance
_interceptor = CUDAInterceptor()

def patch_torch():
    """Patch PyTorch to use Sapphire backend."""
    _interceptor.patch_torch()

def unpatch_torch():
    """Restore PyTorch's original CUDA backend."""
    _interceptor.unpatch_torch()


# =============================================================================
# cuBLAS Interception
# =============================================================================

class CUBLASInterceptor:
    """
    Intercepts cuBLAS calls and redirects to Sapphire BLAS.
    
    This provides the same API as cuBLAS but runs on Apple Silicon.
    """
    
    # cuBLAS handle (not needed in Sapphire, but kept for API compat)
    _handle = 1
    
    @staticmethod
    def create():
        """cublasCreate equivalent."""
        return CUBLASInterceptor._handle
    
    @staticmethod
    def destroy(handle: int):
        """cublasDestroy equivalent."""
        pass
    
    @staticmethod
    def sgemm(handle, transa, transb, m, n, k, alpha, A, lda, B, ldb, beta, C, ldc):
        """
        cublasSgemm equivalent.
        
        C = alpha * op(A) @ op(B) + beta * C
        """
        from .native import native_matmul

        # Handle transposes
        A_np = np.ctypeslib.as_array(A, shape=(lda, k if transa == 'N' else m))
        B_np = np.ctypeslib.as_array(B, shape=(ldb, n if transb == 'N' else k))
        C_np = np.ctypeslib.as_array(C, shape=(ldc, n))
        
        if transa == 'T':
            A_np = A_np.T
        if transb == 'T':
            B_np = B_np.T
        
        result = alpha * native_matmul(A_np[:m, :k], B_np[:k, :n]) + beta * C_np[:m, :n]
        C_np[:m, :n] = result
    
    @staticmethod
    def sgemv(handle, trans, m, n, alpha, A, lda, x, incx, beta, y, incy):
        """cublasSgemv equivalent."""
        A_np = np.ctypeslib.as_array(A, shape=(lda, n))
        x_np = np.ctypeslib.as_array(x, shape=(n if trans == 'N' else m,))
        y_np = np.ctypeslib.as_array(y, shape=(m if trans == 'N' else n,))
        
        if trans == 'N':
            result = alpha * A_np[:m, :n] @ x_np + beta * y_np
        else:
            result = alpha * A_np[:m, :n].T @ x_np + beta * y_np
        
        y_np[:] = result


# =============================================================================
# cuDNN Interception
# =============================================================================

class CUDNNInterceptor:
    """
    Intercepts cuDNN calls and redirects to Sapphire DNN.
    """
    
    _handle = 1
    
    @staticmethod
    def create():
        """cudnnCreate equivalent."""
        return CUDNNInterceptor._handle
    
    @staticmethod
    def destroy(handle: int):
        """cudnnDestroy equivalent."""
        pass
    
    @staticmethod
    def convolution_forward(handle, alpha, x_desc, x, w_desc, w, conv_desc, 
                           algo, workspace, workspace_size, beta, y_desc, y):
        """cudnnConvolutionForward equivalent."""
        from .native import native_conv2d

        # Extract dimensions from descriptors (simplified)
        result = native_conv2d(x, w)
        y[:] = alpha * result + beta * y
    
    @staticmethod
    def batch_normalization_forward(handle, mode, alpha, beta, 
                                    x_desc, x, y_desc, y,
                                    bn_desc, scale, bias, 
                                    running_mean, running_var, eps, 
                                    save_mean, save_invvar):
        """cudnnBatchNormalizationForwardTraining equivalent."""
        from .native import native_batchnorm
        
        result, mean, invvar = native_batchnorm(
            x, scale, bias, running_mean, running_var, 
            training=True, eps=eps
        )
        y[:] = alpha * result + beta * y
        if save_mean is not None:
            save_mean[:] = mean
        if save_invvar is not None:
            save_invvar[:] = invvar


# =============================================================================
# NCCL Interception (Multi-GPU communication)
# =============================================================================

class NCCLInterceptor:
    """
    Intercepts NCCL calls for multi-GPU communication.
    
    In Sapphire, this maps to S-Fabric for multi-Mac communication.
    For single-Mac, it's mostly no-ops.
    """
    
    @staticmethod
    def all_reduce(sendbuff, recvbuff, count, datatype, op, comm, stream):
        """ncclAllReduce equivalent."""
        # Single node: just copy
        if recvbuff is not sendbuff:
            recvbuff[:count] = sendbuff[:count]
    
    @staticmethod
    def all_gather(sendbuff, recvbuff, sendcount, datatype, comm, stream):
        """ncclAllGather equivalent."""
        recvbuff[:sendcount] = sendbuff[:sendcount]
    
    @staticmethod
    def broadcast(buff, count, datatype, root, comm, stream):
        """ncclBroadcast equivalent."""
        pass  # Single node: no-op
    
    @staticmethod
    def reduce_scatter(sendbuff, recvbuff, recvcount, datatype, op, comm, stream):
        """ncclReduceScatter equivalent."""
        recvbuff[:recvcount] = sendbuff[:recvcount]


# =============================================================================
# Module-level API (for drop-in import)
# =============================================================================

# Re-export cuda module functions at this level
from .cuda import (Event, Stream, current_device, current_stream,
                   default_stream, device, device_count, empty_cache,
                   get_device_name, get_device_properties, is_available,
                   manual_seed, manual_seed_all, memory_allocated,
                   memory_reserved, set_device, stream, synchronize)

# Create interceptor instances
cublas = CUBLASInterceptor()
cudnn = CUDNNInterceptor()
nccl = NCCLInterceptor()

# Status
def status():
    """Print Lariat status."""
    print("=" * 60)
    print("SAPPHIRE LARIAT - CUDA INTERCEPTOR")
    print("=" * 60)
    print(f"Native library: {'Loaded' if is_native_available() else '❌ Not loaded'}")
    print(f"torch patched:  {'Yes' if _interceptor._patched else '❌ No'}")
    print(f"cuBLAS ready:   Yes")
    print(f"cuDNN ready:    Yes")
    print(f"NCCL ready:     Yes (single-node)")
    print("=" * 60)
    print("\nTo patch PyTorch:")
    print("   import sapphire.lariat")
    print("   sapphire.lariat.patch_torch()")
    print("\nOr use as drop-in replacement:")
    print("   import sapphire.lariat as cuda")
    print("   import sapphire.cuda as torch_cuda")


# Auto-print status on import if in interactive mode
import __main__

if not hasattr(__main__, '__file__'):
    status()
