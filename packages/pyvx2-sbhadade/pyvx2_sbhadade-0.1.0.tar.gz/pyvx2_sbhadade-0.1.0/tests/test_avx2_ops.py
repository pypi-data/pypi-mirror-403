import numpy as np
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyVX2 import matmul_avx2, add_avx2, mul_avx2, dot_avx2

def test_matmul():
    """Test matrix multiplication correctness"""
    print("\n=== Testing Matrix Multiplication ===")
    
    # Small test
    A = np.random.randn(10, 8).astype(np.float32)
    B = np.random.randn(8, 6).astype(np.float32)
    
    C_avx2 = matmul_avx2(A, B)
    C_numpy = A @ B
    
    assert np.allclose(C_avx2, C_numpy, rtol=1e-5), "Matrix multiplication failed"
    print("✓ Correctness test passed")
    
    # Benchmark
    sizes = [(100, 100, 100), (500, 500, 500), (1000, 500, 800)]
    
    for m, k, n in sizes:
        A = np.random.randn(m, k).astype(np.float32)
        B = np.random.randn(k, n).astype(np.float32)
        
        # Warm up
        _ = matmul_avx2(A, B)
        _ = A @ B
        
        # Benchmark NumPy
        start = time.perf_counter()
        for _ in range(10):
            C_numpy = A @ B
        numpy_time = (time.perf_counter() - start) / 10
        
        # Benchmark AVX2
        start = time.perf_counter()
        for _ in range(10):
            C_avx2 = matmul_avx2(A, B)
        avx2_time = (time.perf_counter() - start) / 10
        
        speedup = numpy_time / avx2_time
        print(f"  {m}x{k} @ {k}x{n}: NumPy={numpy_time*1000:.2f}ms, "
              f"AVX2={avx2_time*1000:.2f}ms, Speedup={speedup:.2f}x")

def test_add():
    """Test vector addition"""
    print("\n=== Testing Vector Addition ===")
    
    a = np.random.randn(1000).astype(np.float32)
    b = np.random.randn(1000).astype(np.float32)
    
    c_avx2 = add_avx2(a, b)
    c_numpy = a + b
    
    assert np.allclose(c_avx2, c_numpy, rtol=1e-6), "Vector addition failed"
    print("✓ Correctness test passed")
    
    # Benchmark
    sizes = [10000, 100000, 1000000]
    for n in sizes:
        a = np.random.randn(n).astype(np.float32)
        b = np.random.randn(n).astype(np.float32)
        
        start = time.perf_counter()
        for _ in range(100):
            c_numpy = a + b
        numpy_time = (time.perf_counter() - start) / 100
        
        start = time.perf_counter()
        for _ in range(100):
            c_avx2 = add_avx2(a, b)
        avx2_time = (time.perf_counter() - start) / 100
        
        speedup = numpy_time / avx2_time
        print(f"  n={n}: NumPy={numpy_time*1000:.3f}ms, "
              f"AVX2={avx2_time*1000:.3f}ms, Speedup={speedup:.2f}x")

def test_mul():
    """Test element-wise multiplication"""
    print("\n=== Testing Element-wise Multiplication ===")
    
    a = np.random.randn(1000).astype(np.float32)
    b = np.random.randn(1000).astype(np.float32)
    
    c_avx2 = mul_avx2(a, b)
    c_numpy = a * b
    
    assert np.allclose(c_avx2, c_numpy, rtol=1e-6), "Multiplication failed"
    print("✓ Correctness test passed")

def test_dot():
    """Test dot product"""
    print("\n=== Testing Dot Product ===")
    
    a = np.random.randn(1000).astype(np.float32)
    b = np.random.randn(1000).astype(np.float32)
    
    result_avx2 = dot_avx2(a, b)
    result_numpy = np.dot(a, b)
    
    assert np.isclose(result_avx2, result_numpy, rtol=1e-5), "Dot product failed"
    print("✓ Correctness test passed")
    
    # Benchmark
    sizes = [10000, 100000, 1000000]
    for n in sizes:
        a = np.random.randn(n).astype(np.float32)
        b = np.random.randn(n).astype(np.float32)
        
        start = time.perf_counter()
        for _ in range(100):
            result_numpy = np.dot(a, b)
        numpy_time = (time.perf_counter() - start) / 100
        
        start = time.perf_counter()
        for _ in range(100):
            result_avx2 = dot_avx2(a, b)
        avx2_time = (time.perf_counter() - start) / 100
        
        speedup = numpy_time / avx2_time
        print(f"  n={n}: NumPy={numpy_time*1000:.3f}ms, "
              f"AVX2={avx2_time*1000:.3f}ms, Speedup={speedup:.2f}x")

if __name__ == "__main__":
    print("PyVX2 Test Suite")
    print("=" * 50)
    
    test_matmul()
    test_add()
    test_mul()
    test_dot()
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")
