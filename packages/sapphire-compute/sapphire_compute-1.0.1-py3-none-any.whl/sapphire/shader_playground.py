import numpy as np
import time
import os
import sys

# Add python dir to path if needed (though we should run as module)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sapphire import unified, Tensor

def load_kernel_source():
    path = os.path.join(os.path.dirname(__file__), '../../Sources/SKL/metal/experimental_kernels.metal')
    with open(path, 'r') as f:
        return f.read()

def main():
    print("SAPPHIRE SHADER PLAYGROUND")
    print("==========================")
    print("loading custom kernels from experimental_kernels.metal...")
    
    source = load_kernel_source()
    
    # ---------------------------------------------------------
    # TEST 1: PRECISION KERNEL: SiLU
    # ---------------------------------------------------------
    print("\n[TEST 1] Precision Kernel: SiLU")
    N = 1024 * 1024 * 10 # 10M elements
    data = np.random.randn(N).astype(np.float32)
    output = np.zeros_like(data)
    
    print(f"  Input size: {N/1e6:.1f} M elements")
    
    # Grid Calculation
    # Kernel processes 1 element per thread (naive)
    # Actually experimental_kernels.metal:sapphire_silu takes float* in, float* out, uint id.
    # So 1 thread per element.
    
    grid_size = (N, 1, 1)
    threadgroup_size = (256, 1, 1)
    
    # Metal grid must be multiple of threads? Or max grid size?
    # Metal: dispatchThreads. (grid_size)
    # threadsPerThreadgroup.
    
    start = time.perf_counter()
    unified.backend.launch_custom_kernel(
        source, "sapphire_silu",
        grid_size, threadgroup_size,
        [data, output] # Buffers
    )
    end = time.perf_counter()
    
    # Verification
    # Python SiLU: x * sigmoid(x)
    ref = data * (1.0 / (1.0 + np.exp(-data)))
    diff = np.abs(output - ref).max()
    
    ops = N * 5 # exp, add, div, mul... approx
    gflops = (ops) / (end - start) / 1e9
    
    print(f"  Execution Time: {(end-start)*1000:.2f} ms")
    print(f"  Throughput: {gflops:.2f} GFLOPS (Effective)")
    print(f"  Max Diff: {diff:.6f}")
    
    if diff < 1e-4:
        print("  VERIFICATION: PASS")
    else:
        print("  VERIFICATION: FAIL")

    # ---------------------------------------------------------
    # TEST 2: SIMD-GROUP GEMM (EXPERIMENTAL)
    # ---------------------------------------------------------
    print("\n[TEST 2] SIMD-Group GEMM (Experimental)")
    M, N, K = 1024, 1024, 1024
    print(f"  Matrix: {M}x{N}x{K}")
    
    A = np.random.randn(M, K).astype(np.float32)
    B = np.random.randn(K, N).astype(np.float32)
    C = np.zeros((M, N), dtype=np.float32)
    
    # Grid logic for 'sapphire_gemm_simdgroup'
    # It assumes SIMD groups. 
    # Let's say we launch (N, M, 1) threads?
    # Kernel uses gid.x, gid.y.
    
    grid_size_gemm = (N, M, 1)
    group_size_gemm = (32, 32, 1) # 1024 threads per group? Max is 1024 on M4.
    
    # Pass scalars as 1-element arrays
    M_arr = np.array([M], dtype=np.int32)
    N_arr = np.array([N], dtype=np.int32)
    K_arr = np.array([K], dtype=np.int32)
    
    start = time.perf_counter()
    unified.backend.launch_custom_kernel(
        source, "sapphire_gemm_simdgroup",
        grid_size_gemm, group_size_gemm,
        [A, B, C, M_arr, N_arr, K_arr]
    )
    end = time.perf_counter()
    
    gflops = (2*M*N*K) / (end - start) / 1e9
    print(f"  Speed: {gflops:.2f} GFLOPS")
    
    # Verify center element
    ref = np.dot(A[M//2], B[:, N//2])
    val = C[M//2, N//2]
    print(f"  Ref: {ref:.4f}, Val: {val:.4f}")

if __name__ == "__main__":
    main()
