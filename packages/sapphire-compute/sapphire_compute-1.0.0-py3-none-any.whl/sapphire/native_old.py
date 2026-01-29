"""
SAPPHIRE NATIVE LIBRARY INTERFACE
=================================

Direct FFI bindings to libsapphire.dylib - our CUDA killer.
Correct ctypes signatures matching exact C function declarations.
"""

import ctypes
import os
from ctypes import (POINTER, c_double, c_float, c_int, c_int8, c_size_t,
                    c_uint8, c_uint16, c_void_p)

import numpy as np

_lib = None
_lib_loaded = False

def _find_library():
    """Find libsapphire.dylib"""
    search_paths = [
        os.path.join(os.path.dirname(__file__), 'lib', 'libsapphire.dylib'),
        os.path.join(os.path.dirname(__file__), '..', '..', '.build', 'release', 'libSapphireNative.dylib'),
        '/usr/local/lib/libsapphire.dylib',
    ]
    for path in search_paths:
        if os.path.exists(path):
            return path
    return None

def _load_library():
    global _lib, _lib_loaded
    if _lib_loaded:
        return
    
    lib_path = _find_library()
    if lib_path is None:
        raise RuntimeError("libsapphire.dylib not found")
    
    _lib = ctypes.CDLL(lib_path)
    _setup_function_signatures()
    _lib_loaded = True

def _setup_function_signatures():
    """Setup ctypes signatures matching exact C declarations"""
    global _lib
    
    # ========== Memory ==========
    _lib.sapphire_aligned_alloc.argtypes = [c_size_t]
    _lib.sapphire_aligned_alloc.restype = c_void_p
    _lib.sapphire_aligned_free.argtypes = [c_void_p]
    
    # ========== AMX Info ==========
    _lib.sapphire_amx_available.restype = c_int
    _lib.sapphire_amx_tile_size.restype = c_int
    
    # ========== BLAS Level 1 ==========
    # void sapphire_saxpy(int n, float alpha, const float *x, int incx, float *y, int incy)
    _lib.sapphire_saxpy.argtypes = [c_int, c_float, POINTER(c_float), c_int, POINTER(c_float), c_int]
    # float sapphire_sdot(int n, const float *x, int incx, const float *y, int incy)
    _lib.sapphire_sdot.argtypes = [c_int, POINTER(c_float), c_int, POINTER(c_float), c_int]
    _lib.sapphire_sdot.restype = c_float
    # float sapphire_snrm2(int n, const float *x, int incx)
    _lib.sapphire_snrm2.argtypes = [c_int, POINTER(c_float), c_int]
    _lib.sapphire_snrm2.restype = c_float
    # float sapphire_sasum(int n, const float *x, int incx)
    _lib.sapphire_sasum.argtypes = [c_int, POINTER(c_float), c_int]
    _lib.sapphire_sasum.restype = c_float
    # int sapphire_isamax(int n, const float *x, int incx)
    _lib.sapphire_isamax.argtypes = [c_int, POINTER(c_float), c_int]
    _lib.sapphire_isamax.restype = c_int
    # void sapphire_sscal(int n, float alpha, float *x, int incx)
    _lib.sapphire_sscal.argtypes = [c_int, c_float, POINTER(c_float), c_int]
    # void sapphire_scopy(int n, const float *x, int incx, float *y, int incy)
    _lib.sapphire_scopy.argtypes = [c_int, POINTER(c_float), c_int, POINTER(c_float), c_int]
    # void sapphire_sswap(int n, float *x, int incx, float *y, int incy)
    _lib.sapphire_sswap.argtypes = [c_int, POINTER(c_float), c_int, POINTER(c_float), c_int]
    
    # ========== BLAS Level 3 (CORRECT SIGNATURES) ==========
    # void sapphire_sgemm(int M, int N, int K, float alpha, const float *A, int lda,
    #                     const float *B, int ldb, float beta, float *C, int ldc)
    _lib.sapphire_sgemm.argtypes = [
        c_int, c_int, c_int,        # M, N, K
        c_float,                     # alpha
        POINTER(c_float), c_int,     # A, lda
        POINTER(c_float), c_int,     # B, ldb
        c_float,                     # beta
        POINTER(c_float), c_int      # C, ldc
    ]
    
    _lib.sapphire_sgemm_amx.argtypes = [
        c_int, c_int, c_int,        # M, N, K
        c_float,                     # alpha
        POINTER(c_float), c_int,     # A, lda
        POINTER(c_float), c_int,     # B, ldb
        c_float,                     # beta
        POINTER(c_float), c_int      # C, ldc
    ]
    
    _lib.sapphire_sgemm_relu_fused.argtypes = [
        c_int, c_int, c_int,        # M, N, K
        c_float,                     # alpha
        POINTER(c_float), c_int,     # A, lda
        POINTER(c_float), c_int,     # B, ldb
        c_float,                     # beta
        POINTER(c_float), c_int      # C, ldc
    ]
    
    _lib.sapphire_sgemm_gelu_fused.argtypes = [
        c_int, c_int, c_int,        # M, N, K
        c_float,                     # alpha
        POINTER(c_float), c_int,     # A, lda
        POINTER(c_float), c_int,     # B, ldb
        c_float,                     # beta
        POINTER(c_float), c_int      # C, ldc
    ]
    
    # ========== Activations (IN-PLACE - 2 args!) ==========
    # void sapphire_relu(float *x, size_t n)
    _lib.sapphire_relu.argtypes = [POINTER(c_float), c_size_t]
    # void sapphire_gelu(float *x, size_t n)
    _lib.sapphire_gelu.argtypes = [POINTER(c_float), c_size_t]
    # void sapphire_silu(float *x, size_t n)
    _lib.sapphire_silu.argtypes = [POINTER(c_float), c_size_t]
    
    # ========== Softmax (OUT-OF-PLACE) ==========
    # void sapphire_softmax(float *output, const float *input, int batch_size, int seq_len)
    _lib.sapphire_softmax.argtypes = [POINTER(c_float), POINTER(c_float), c_int, c_int]
    
    # ========== Normalization (OUT-OF-PLACE) ==========
    # void sapphire_layer_norm(float *output, const float *input, const float *gamma,
    #                          const float *beta, int batch_size, int hidden_size, float eps)
    _lib.sapphire_layer_norm.argtypes = [
        POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float),
        c_int, c_int, c_float
    ]
    # void sapphire_rms_norm(float *output, const float *input, const float *weight,
    #                        int batch_size, int hidden_size, float eps)
    _lib.sapphire_rms_norm.argtypes = [
        POINTER(c_float), POINTER(c_float), POINTER(c_float),
        c_int, c_int, c_float
    ]
    
    # ========== Attention ==========
    # void sapphire_attention(const float *Q, const float *K, const float *V, float *output,
    #                         int batch, int heads, int seq, int head_dim, float scale)
    _lib.sapphire_attention.argtypes = [
        POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float),
        c_int, c_int, c_int, c_int, c_float
    ]
    # void sapphire_flash_attention(const float *Q, const float *K, const float *V, float *output,
    #                               int batch, int heads, int seq, int head_dim, float scale, int block_size)
    _lib.sapphire_flash_attention.argtypes = [
        POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float),
        c_int, c_int, c_int, c_int, c_float, c_int
    ]
    
    # ========== Linear Algebra (LAPACK) ==========
    _lib.sapphire_getrf.argtypes = [POINTER(c_float), POINTER(c_int), c_int]
    _lib.sapphire_getrf.restype = c_int
    _lib.sapphire_getri.argtypes = [POINTER(c_float), POINTER(c_int), c_int]
    _lib.sapphire_getri.restype = c_int
    _lib.sapphire_gesvd.argtypes = [
        POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int
    ]
    _lib.sapphire_gesvd.restype = c_int
    _lib.sapphire_syevd.argtypes = [POINTER(c_float), POINTER(c_float), c_int]
    _lib.sapphire_syevd.restype = c_int
    _lib.sapphire_det.argtypes = [POINTER(c_float), c_int]
    _lib.sapphire_det.restype = c_float
    
    # Note: benchmark functions removed (not in this library build)


# =============================================================================
# HIGH-LEVEL PYTHON API
# =============================================================================

def is_native_available():
    """Check if native library is available"""
    try:
        _load_library()
        return True
    except:
        return False

def get_lib():
    """Get the loaded library"""
    _load_library()
    return _lib

def amx_available():
    """Check if AMX is available"""
    _load_library()
    return _lib.sapphire_amx_available() != 0

# =============================================================================
# SGEMM Wrappers
# =============================================================================

def sgemm(A: np.ndarray, B: np.ndarray, alpha=1.0, beta=0.0, use_amx=True):
    """Matrix multiplication: C = alpha * A @ B + beta * C"""
    _load_library()
    
    A = np.ascontiguousarray(A.astype(np.float32))
    B = np.ascontiguousarray(B.astype(np.float32))
    
    M, K = A.shape
    K2, N = B.shape
    assert K == K2, f"Matrix dimensions incompatible: A({M}x{K}) @ B({K2}x{N})"
    
    C = np.zeros((M, N), dtype=np.float32)
    
    A_ptr = A.ctypes.data_as(POINTER(c_float))
    B_ptr = B.ctypes.data_as(POINTER(c_float))
    C_ptr = C.ctypes.data_as(POINTER(c_float))
    
    if use_amx:
        _lib.sapphire_sgemm_amx(
            c_int(M), c_int(N), c_int(K),
            c_float(alpha),
            A_ptr, c_int(K),
            B_ptr, c_int(N),
            c_float(beta),
            C_ptr, c_int(N)
        )
    else:
        _lib.sapphire_sgemm(
            c_int(M), c_int(N), c_int(K),
            c_float(alpha),
            A_ptr, c_int(K),
            B_ptr, c_int(N),
            c_float(beta),
            C_ptr, c_int(N)
        )
    
    return C

def sgemm_relu_fused(A: np.ndarray, B: np.ndarray, alpha=1.0, beta=0.0):
    """Fused GEMM + ReLU: C = ReLU(alpha * A @ B + beta * C)"""
    _load_library()
    
    A = np.ascontiguousarray(A.astype(np.float32))
    B = np.ascontiguousarray(B.astype(np.float32))
    
    M, K = A.shape
    K2, N = B.shape
    assert K == K2
    
    C = np.zeros((M, N), dtype=np.float32)
    
    _lib.sapphire_sgemm_relu_fused(
        c_int(M), c_int(N), c_int(K),
        c_float(alpha),
        A.ctypes.data_as(POINTER(c_float)), c_int(K),
        B.ctypes.data_as(POINTER(c_float)), c_int(N),
        c_float(beta),
        C.ctypes.data_as(POINTER(c_float)), c_int(N)
    )
    return C

def sgemm_gelu_fused(A: np.ndarray, B: np.ndarray, alpha=1.0, beta=0.0):
    """Fused GEMM + GELU: C = GELU(alpha * A @ B + beta * C)"""
    _load_library()
    
    A = np.ascontiguousarray(A.astype(np.float32))
    B = np.ascontiguousarray(B.astype(np.float32))
    
    M, K = A.shape
    K2, N = B.shape
    assert K == K2
    
    C = np.zeros((M, N), dtype=np.float32)
    
    _lib.sapphire_sgemm_gelu_fused(
        c_int(M), c_int(N), c_int(K),
        c_float(alpha),
        A.ctypes.data_as(POINTER(c_float)), c_int(K),
        B.ctypes.data_as(POINTER(c_float)), c_int(N),
        c_float(beta),
        C.ctypes.data_as(POINTER(c_float)), c_int(N)
    )
    return C

# =============================================================================
# Activation Wrappers (IN-PLACE operations)
# =============================================================================

def relu(x: np.ndarray):
    """ReLU activation: max(0, x) - IN-PLACE"""
    _load_library()
    out = np.ascontiguousarray(x.astype(np.float32)).copy()
    _lib.sapphire_relu(
        out.ctypes.data_as(POINTER(c_float)),
        c_size_t(out.size)
    )
    return out

def gelu(x: np.ndarray):
    """GELU activation - IN-PLACE"""
    _load_library()
    out = np.ascontiguousarray(x.astype(np.float32)).copy()
    _lib.sapphire_gelu(
        out.ctypes.data_as(POINTER(c_float)),
        c_size_t(out.size)
    )
    return out

def silu(x: np.ndarray):
    """SiLU (Swish) activation - IN-PLACE"""
    _load_library()
    out = np.ascontiguousarray(x.astype(np.float32)).copy()
    _lib.sapphire_silu(
        out.ctypes.data_as(POINTER(c_float)),
        c_size_t(out.size)
    )
    return out

def softmax(x: np.ndarray):
    """Softmax activation along last axis"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    
    if x.ndim == 1:
        batch, seq = 1, x.size
        x = x.reshape(1, -1)
    else:
        batch, seq = x.shape[0], x.shape[-1]
        x = x.reshape(-1, seq)
        batch = x.shape[0]
    
    out = np.zeros_like(x)
    _lib.sapphire_softmax(
        out.ctypes.data_as(POINTER(c_float)),
        x.ctypes.data_as(POINTER(c_float)),
        c_int(batch), c_int(seq)
    )
    return out

# =============================================================================
# Normalization Wrappers
# =============================================================================

def layer_norm(x: np.ndarray, gamma: np.ndarray = None, beta: np.ndarray = None, eps=1e-5):
    """Layer normalization"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    
    if x.ndim == 1:
        batch, hidden = 1, x.size
        x = x.reshape(1, -1)
    else:
        batch, hidden = x.shape[0], x.shape[-1]
    
    if gamma is None:
        gamma = np.ones(hidden, dtype=np.float32)
    if beta is None:
        beta = np.zeros(hidden, dtype=np.float32)
    
    gamma = np.ascontiguousarray(gamma.astype(np.float32))
    beta = np.ascontiguousarray(beta.astype(np.float32))
    out = np.zeros_like(x)
    
    _lib.sapphire_layer_norm(
        out.ctypes.data_as(POINTER(c_float)),
        x.ctypes.data_as(POINTER(c_float)),
        gamma.ctypes.data_as(POINTER(c_float)),
        beta.ctypes.data_as(POINTER(c_float)),
        c_int(batch), c_int(hidden), c_float(eps)
    )
    return out

def rms_norm(x: np.ndarray, gamma: np.ndarray = None, eps=1e-5):
    """RMS normalization (used in LLaMA, Gemma)"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    
    if x.ndim == 1:
        batch, hidden = 1, x.size
        x = x.reshape(1, -1)
    else:
        batch, hidden = x.shape[0], x.shape[-1]
    
    if gamma is None:
        gamma = np.ones(hidden, dtype=np.float32)
    
    gamma = np.ascontiguousarray(gamma.astype(np.float32))
    out = np.zeros_like(x)
    
    _lib.sapphire_rms_norm(
        out.ctypes.data_as(POINTER(c_float)),
        x.ctypes.data_as(POINTER(c_float)),
        gamma.ctypes.data_as(POINTER(c_float)),
        c_int(batch), c_int(hidden), c_float(eps)
    )
    return out

# =============================================================================
# Attention Wrappers
# =============================================================================

def attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray, scale=None):
    """Standard scaled dot-product attention."""
    _load_library()
    
    Q = np.ascontiguousarray(Q.astype(np.float32))
    K = np.ascontiguousarray(K.astype(np.float32))
    V = np.ascontiguousarray(V.astype(np.float32))
    
    orig_shape = Q.shape
    if Q.ndim == 2:
        batch, heads, seq, head_dim = 1, 1, Q.shape[0], Q.shape[1]
        Q = Q.reshape(1, 1, seq, head_dim)
        K = K.reshape(1, 1, seq, head_dim)
        V = V.reshape(1, 1, seq, head_dim)
    elif Q.ndim == 3:
        batch, heads, seq, head_dim = 1, Q.shape[0], Q.shape[1], Q.shape[2]
        Q = Q.reshape(1, heads, seq, head_dim)
        K = K.reshape(1, heads, seq, head_dim)
        V = V.reshape(1, heads, seq, head_dim)
    else:
        batch, heads, seq, head_dim = Q.shape
    
    if scale is None:
        scale = 1.0 / np.sqrt(head_dim)
    
    out = np.zeros_like(Q)
    
    _lib.sapphire_attention(
        Q.ctypes.data_as(POINTER(c_float)),
        K.ctypes.data_as(POINTER(c_float)),
        V.ctypes.data_as(POINTER(c_float)),
        out.ctypes.data_as(POINTER(c_float)),
        c_int(batch), c_int(heads), c_int(seq), c_int(head_dim),
        c_float(scale)
    )
    
    return out.reshape(orig_shape)

def flash_attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray, scale=None, block_size=64):
    """Flash Attention - memory efficient attention."""
    _load_library()
    
    Q = np.ascontiguousarray(Q.astype(np.float32))
    K = np.ascontiguousarray(K.astype(np.float32))
    V = np.ascontiguousarray(V.astype(np.float32))
    
    orig_shape = Q.shape
    if Q.ndim == 2:
        batch, heads, seq, head_dim = 1, 1, Q.shape[0], Q.shape[1]
        Q = Q.reshape(1, 1, seq, head_dim)
        K = K.reshape(1, 1, seq, head_dim)
        V = V.reshape(1, 1, seq, head_dim)
    elif Q.ndim == 3:
        batch, heads, seq, head_dim = 1, Q.shape[0], Q.shape[1], Q.shape[2]
        Q = Q.reshape(1, heads, seq, head_dim)
        K = K.reshape(1, heads, seq, head_dim)
        V = V.reshape(1, heads, seq, head_dim)
    else:
        batch, heads, seq, head_dim = Q.shape
    
    if scale is None:
        scale = 1.0 / np.sqrt(head_dim)
    
    out = np.zeros_like(Q)
    
    _lib.sapphire_flash_attention(
        Q.ctypes.data_as(POINTER(c_float)),
        K.ctypes.data_as(POINTER(c_float)),
        V.ctypes.data_as(POINTER(c_float)),
        out.ctypes.data_as(POINTER(c_float)),
        c_int(batch), c_int(heads), c_int(seq), c_int(head_dim),
        c_float(scale), c_int(block_size)
    )
    
    return out.reshape(orig_shape)

# =============================================================================
# BLAS Level 1 Wrappers
# =============================================================================

def saxpy(alpha: float, x: np.ndarray, y: np.ndarray):
    """SAXPY: y = alpha * x + y"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    y = np.ascontiguousarray(y.astype(np.float32)).copy()
    
    _lib.sapphire_saxpy(
        c_int(x.size), c_float(alpha),
        x.ctypes.data_as(POINTER(c_float)), c_int(1),
        y.ctypes.data_as(POINTER(c_float)), c_int(1)
    )
    return y

def sdot(x: np.ndarray, y: np.ndarray):
    """SDOT: dot product of x and y"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    y = np.ascontiguousarray(y.astype(np.float32))
    
    return _lib.sapphire_sdot(
        c_int(x.size),
        x.ctypes.data_as(POINTER(c_float)), c_int(1),
        y.ctypes.data_as(POINTER(c_float)), c_int(1)
    )

def snrm2(x: np.ndarray):
    """SNRM2: Euclidean norm of x"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    
    return _lib.sapphire_snrm2(
        c_int(x.size),
        x.ctypes.data_as(POINTER(c_float)), c_int(1)
    )

def sasum(x: np.ndarray):
    """SASUM: sum of absolute values"""
    _load_library()
    x = np.ascontiguousarray(x.astype(np.float32))
    
    return _lib.sapphire_sasum(
        c_int(x.size),
        x.ctypes.data_as(POINTER(c_float)), c_int(1)
    )

# =============================================================================
# Linear Algebra (LAPACK) Wrappers
# =============================================================================

def svd(A: np.ndarray):
    """Singular Value Decomposition: A = U @ diag(S) @ VT"""
    _load_library()
    A = np.ascontiguousarray(A.astype(np.float32)).copy()
    m, n = A.shape
    k = min(m, n)
    
    S = np.zeros(k, dtype=np.float32)
    U = np.zeros((m, m), dtype=np.float32)
    VT = np.zeros((n, n), dtype=np.float32)
    
    ret = _lib.sapphire_gesvd(
        A.ctypes.data_as(POINTER(c_float)),
        S.ctypes.data_as(POINTER(c_float)),
        U.ctypes.data_as(POINTER(c_float)),
        VT.ctypes.data_as(POINTER(c_float)),
        c_int(m), c_int(n)
    )
    
    if ret != 0:
        raise RuntimeError(f"SVD failed with error code {ret}")
    
    return U[:, :k], S, VT[:k, :]

def eig(A: np.ndarray):
    """Eigenvalue decomposition for symmetric matrices"""
    _load_library()
    A = np.ascontiguousarray(A.astype(np.float32)).copy()
    n = A.shape[0]
    
    eigenvalues = np.zeros(n, dtype=np.float32)
    
    ret = _lib.sapphire_syevd(
        A.ctypes.data_as(POINTER(c_float)),
        eigenvalues.ctypes.data_as(POINTER(c_float)),
        c_int(n)
    )
    
    if ret != 0:
        raise RuntimeError(f"Eigenvalue decomposition failed with error code {ret}")
    
    return eigenvalues, A

def inv(A: np.ndarray):
    """Matrix inverse using LU decomposition"""
    _load_library()
    A = np.ascontiguousarray(A.astype(np.float32)).copy()
    n = A.shape[0]
    ipiv = np.zeros(n, dtype=np.int32)
    
    ret = _lib.sapphire_getrf(
        A.ctypes.data_as(POINTER(c_float)),
        ipiv.ctypes.data_as(POINTER(c_int)),
        c_int(n)
    )
    if ret != 0:
        raise RuntimeError(f"LU factorization failed with error code {ret}")
    
    ret = _lib.sapphire_getri(
        A.ctypes.data_as(POINTER(c_float)),
        ipiv.ctypes.data_as(POINTER(c_int)),
        c_int(n)
    )
    if ret != 0:
        raise RuntimeError(f"Matrix inversion failed with error code {ret}")
    
    return A

def det(A: np.ndarray):
    """Matrix determinant"""
    _load_library()
    A = np.ascontiguousarray(A.astype(np.float32)).copy()
    n = A.shape[0]
    
    return _lib.sapphire_det(
        A.ctypes.data_as(POINTER(c_float)),
        c_int(n)
    )

# Note: benchmark_sgemm and benchmark_sgemm_amx functions removed (not in this library build)
