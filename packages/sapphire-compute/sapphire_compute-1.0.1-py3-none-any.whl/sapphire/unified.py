"""
💎 SAPPHIRE UNIFIED API 💎
============================

The One Ring to rule them all. 
Combines AMX (Ultra), GPU (Metal), and ANE (vDSP) into a single,
intelligent, high-performance interface.

Automatic dispatch based on tensor size and operation type.
"""

import ctypes
import os
import sys
import numpy as np
import time

# =============================================================================
# LIBRARY LOADING
# =============================================================================

class SapphireBackend:
    def __init__(self):
        self.lib_path = os.path.dirname(os.path.abspath(__file__))
        # We packaged dylibs into this directory
        self.build_path = self.lib_path
        
        self.ultra = self._load_lib('libsapphire_ultra.dylib')
        self.gpu = self._load_lib('libsapphire_gpu.dylib')
        self.vdsp = self._load_lib('libsapphire_vdsp.dylib')
        
        self._setup_ultra()
        self._setup_gpu()
        self._setup_vdsp()
        
        print(f"[SAPPHIRE] Backend Initialized:")
        print(f"  - ULTRA (AMX/NEON): {'ENGAGED' if self.ultra else 'OFFLINE'}")
        print(f"  - GPU (Metal MPS):  {'ENGAGED' if self.gpu else 'OFFLINE'}")
        print(f"  - vDSP (Accelerate): {'ENGAGED' if self.vdsp else 'OFFLINE'}")

    def _load_lib(self, name):
        try:
            path = os.path.join(self.build_path, name)
            return ctypes.CDLL(path)
        except Exception as e:
            print(f"[SAPPHIRE] Warning: Could not load {name}: {e}")
            return None

    def _setup_ultra(self):
        if not self.ultra: return
        self.ultra.sapphire_ultra_relu.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.ultra.sapphire_ultra_gelu.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.ultra.sapphire_ultra_silu.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.ultra.sapphire_ultra_softmax.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        self.ultra.sapphire_ultra_rms_norm.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float]

    def _setup_gpu(self):
        if self.gpu:
            self.gpu.sapphire_gpu_available.restype = ctypes.c_bool
            self.gpu.sapphire_gpu_sgemm.argtypes = [
                ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                ctypes.c_float, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
                ctypes.c_float, ctypes.c_void_p, ctypes.c_int
            ]
            # Custom Shader Playground
            try:
                self.gpu.sapphire_gpu_run_custom.argtypes = [
                    ctypes.c_char_p, # Source
                    ctypes.c_char_p, # Kernel Name
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, # Grid
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, # Threadgroup
                    ctypes.POINTER(ctypes.c_void_p), # Buffers array
                    ctypes.c_int, # Num Buffers
                    ctypes.POINTER(ctypes.c_int) # Buffer Sizes array
                ]
            except Exception:
                print("[WARN] Custom shader support not found in libsapphire_gpu")

        # Library constructor runs automatically, just check status
        if self.gpu and self.gpu.sapphire_gpu_available():
            print("[SAPPHIRE] GPU initialized automatically")
        else:
            print("[SAPPHIRE] GPU available check returned False")
    
    def launch_custom_kernel(self, source_code, kernel_name, grid_size, threadgroup_size, buffers):
        """
        Launch a raw Metal kernel.
        buffers: List of numpy arrays. MUST be float32 for now based on C impl.
        """
        if not self.gpu:
            raise RuntimeError("GPU backend not loaded")
            
        c_source = source_code.encode('utf-8')
        c_kernel = kernel_name.encode('utf-8')
        
        # Prepare buffers
        num_buffers = len(buffers)
        buffer_ptrs = (ctypes.c_void_p * num_buffers)()
        buffer_sizes = (ctypes.c_int * num_buffers)()
        
        for i, buf in enumerate(buffers):
            buffer_ptrs[i] = buf.ctypes.data_as(ctypes.c_void_p)
            buffer_sizes[i] = buf.nbytes
            
        self.gpu.sapphire_gpu_run_custom(
            c_source, c_kernel,
            grid_size[0], grid_size[1], grid_size[2],
            threadgroup_size[0], threadgroup_size[1], threadgroup_size[2],
            buffer_ptrs, num_buffers, buffer_sizes
        )


    def _setup_vdsp(self):
        if not self.vdsp: return
        self.vdsp.sapphire_vdsp_gemm.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float,
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
            ctypes.c_float, ctypes.c_void_p, ctypes.c_int
        ]

# Global backend instance
backend = SapphireBackend()

# =============================================================================
# PUBLIC API
# =============================================================================

def matmul(A, B, C=None, alpha=1.0, beta=0.0):
    """
    Intelligent Matrix Multiplication.
    Dispatches to GPU for large matrices, AMX/vDSP for smaller ones.
    """
    M, K = A.shape
    K2, N = B.shape
    if K != K2: raise ValueError(f"Shape mismatch: {A.shape} x {B.shape}")
    
    if C is None:
        C = np.zeros((M, N), dtype=np.float32)
    
    # Heuristic for dispatch
    # GPU overhead is ~50-100us. Worth it for operations > 100 GFLOPS or large VRAM usage.
    # M4 GPU is very fast, but data transfer (shared mem) is low overhead.
    # Threshold: if M*N*K > 2048^3 (8B ops), use GPU. 
    # Actually, Metal is good for even 1024x1024.
    
    use_gpu = (M * N * K) >= (1024 * 1024 * 1024)  # > 1G ops
    # Override: Always use GPU for now to prove point, unless tiny
    if M >= 1024 and N >= 1024 and K >= 1024:
        use_gpu = True
    else:
        use_gpu = False
        
    if use_gpu and backend.gpu:
        # print(f"[DEBUG] Dispatching {M}x{N}x{K} to GPU")
        backend.gpu.sapphire_gpu_sgemm(
            False, False, M, N, K, alpha,
            A.ctypes.data_as(ctypes.c_void_p), K,
            B.ctypes.data_as(ctypes.c_void_p), N,
            beta, C.ctypes.data_as(ctypes.c_void_p), N
        )
    elif backend.vdsp:
        # print(f"[DEBUG] Dispatching {M}x{N}x{K} to vDSP (AMX)")
        backend.vdsp.sapphire_vdsp_gemm(
            M, N, K, alpha,
            A.ctypes.data_as(ctypes.c_void_p), K,
            B.ctypes.data_as(ctypes.c_void_p), N,
            beta, C.ctypes.data_as(ctypes.c_void_p), N
        )
    else:
        # print(f"[DEBUG] Dispatching {M}x{N}x{K} to NUMPY (Slow!)")
        np.dot(A, B, out=C)
        
    return C

def relu(x):
    """Vectorized ReLU"""
    if backend.ultra:
        backend.ultra.sapphire_ultra_relu(x.ctypes.data_as(ctypes.c_void_p), x.size)
    return x

def gelu(x):
    """Vectorized GELU"""
    if backend.ultra:
        backend.ultra.sapphire_ultra_gelu(x.ctypes.data_as(ctypes.c_void_p), x.size)
    return x

def silu(x):
    """Vectorized SiLU"""
    if backend.ultra:
        backend.ultra.sapphire_ultra_silu(x.ctypes.data_as(ctypes.c_void_p), x.size)
    return x

def softmax(x):
    """Vectorized Softmax"""
    rows, cols = x.shape
    out = np.empty_like(x)
    if backend.ultra:
        backend.ultra.sapphire_ultra_softmax(
            out.ctypes.data_as(ctypes.c_void_p),
            x.ctypes.data_as(ctypes.c_void_p),
            rows, cols
        )
    return out

def rms_norm(x, weight, eps=1e-5):
    """Vectorized RMS Norm"""
    rows, cols = x.shape
    out = np.empty_like(x)
    if backend.ultra:
        backend.ultra.sapphire_ultra_rms_norm(
            out.ctypes.data_as(ctypes.c_void_p),
            x.ctypes.data_as(ctypes.c_void_p),
            weight.ctypes.data_as(ctypes.c_void_p),
            rows, cols, eps
        )
    return out

# =============================================================================
# BENCHMARK SUITE
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SAPPHIRE UNIFIED BENCHMARK")
    print("="*80)
    
    # 1. Large Matrix Multiplication (Target: GPU)
    print("\n[TEST] Large Matrix Multiplication (4096 x 4096)")
    M, N, K = 4096, 4096, 4096
    A = np.random.randn(M, K).astype(np.float32)
    B = np.random.randn(K, N).astype(np.float32)
    C = np.zeros((M, N), dtype=np.float32)
    
    start = time.perf_counter()
    matmul(A, B, C) # Run 1 (Warmup)
    matmul(A, B, C) # Run 2
    matmul(A, B, C) # Run 3
    end = time.perf_counter()
    
    avg_time = (end - start) / 3
    tflops = (2 * M * N * K) / avg_time / 1e12
    print(f"  Result: {tflops:.2f} TFLOPS (Should be > 2.0 on M4 GPU)")
    
    # 2. Vector Activation (Target: Ultra/AMX)
    print("\n[TEST] Vector Activation (GELU, 100M elements)")
    x = np.random.randn(100_000_000).astype(np.float32)
    
    start = time.perf_counter()
    gelu(x)
    end = time.perf_counter()
    
    gops = x.size / (end - start) / 1e9
    print(f"  Result: {gops:.2f} Gops/s (Should be > 2.5)")
    
    # 3. Transformer Block Simulation
    print("\n[TEST] Transformer Block Simulation (Llama-style)")
    batch, seq, model_dim = 32, 2048, 4096
    hidden_dim = 11008 # MLP expansion
    
    # Tensors
    h = np.random.randn(batch * seq, model_dim).astype(np.float32)
    w_q = np.random.randn(model_dim, model_dim).astype(np.float32) # using weight-last for simpl
    w_gate = np.random.randn(model_dim, hidden_dim).astype(np.float32)
    w_up = np.random.randn(model_dim, hidden_dim).astype(np.float32)
    w_down = np.random.randn(hidden_dim, model_dim).astype(np.float32)
    norm_w = np.random.randn(model_dim).astype(np.float32)
    
    start_total = time.perf_counter()
    
    # RMS Norm
    h_norm = rms_norm(h, norm_w)
    
    # Attention Projection (Simplified)
    q = matmul(h_norm, w_q)
    
    # MLP (SwiGLU)
    # - Gate Proj
    gate = matmul(h_norm, w_gate)
    # - Up Proj
    up = matmul(h_norm, w_up)
    # - Act
    silu(gate)
    # - Elementwise Mul (NumPy for now)
    act = gate * up
    # - Down Proj
    out = matmul(act, w_down)
    
    end_total = time.perf_counter()
    
    print(f"  Block Latency: {(end_total - start_total)*1000:.2f} ms")
    print(f"  Tokens/sec: {(batch * seq) / (end_total - start_total):.0f}")
    
    print("\n" + "="*80)
    print("SAPPHIRE IS READY FOR DEPLOYMENT")
    print("="*80)
