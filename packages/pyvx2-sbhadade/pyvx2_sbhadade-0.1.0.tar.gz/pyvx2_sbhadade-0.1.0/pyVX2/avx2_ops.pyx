# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as np

# AVX2 intrinsics
cdef extern from "immintrin.h":
    ctypedef float __m256 "__m256"
    
    __m256 _mm256_setzero_ps()
    __m256 _mm256_load_ps(const float* mem_addr)
    __m256 _mm256_loadu_ps(const float* mem_addr)
    void _mm256_store_ps(float* mem_addr, __m256 a)
    void _mm256_storeu_ps(float* mem_addr, __m256 a)
    __m256 _mm256_add_ps(__m256 a, __m256 b)
    __m256 _mm256_mul_ps(__m256 a, __m256 b)
    __m256 _mm256_fmadd_ps(__m256 a, __m256 b, __m256 c)
    __m256 _mm256_broadcast_ss(const float* mem_addr)

def matmul_avx2(np.ndarray[np.float32_t, ndim=2] A, 
                np.ndarray[np.float32_t, ndim=2] B):
    """
    AVX2-accelerated matrix multiplication: C = A @ B
    
    Parameters:
    -----------
    A : numpy.ndarray (M, K) float32
    B : numpy.ndarray (K, N) float32
    
    Returns:
    --------
    C : numpy.ndarray (M, N) float32
    """
    cdef int M = A.shape[0]
    cdef int K = A.shape[1]
    cdef int N = B.shape[1]
    
    if A.shape[1] != B.shape[0]:
        raise ValueError("Incompatible matrix shapes for multiplication: (%d,%d) @ (%d,%d)" % 
                        (A.shape[0], A.shape[1], B.shape[0], B.shape[1]))
    
    # Create output array
    cdef np.ndarray[np.float32_t, ndim=2] C = np.zeros((M, N), dtype=np.float32)
    
    cdef int i, j, k
    cdef __m256 va, vb, vc
    cdef float temp[8]
    cdef float sum
    cdef int k_block
    
    # Transpose B for better cache locality
    cdef np.ndarray[np.float32_t, ndim=2] BT = np.ascontiguousarray(B.T)
    
    for i in range(M):
        for j in range(N):
            sum = 0.0
            vc = _mm256_setzero_ps()
            
            # Process 8 elements at a time using AVX2
            k_block = (K // 8) * 8
            for k in range(0, k_block, 8):
                va = _mm256_loadu_ps(&A[i, k])
                vb = _mm256_loadu_ps(&BT[j, k])
                vc = _mm256_fmadd_ps(va, vb, vc)
            
            # Horizontal sum of the 8 accumulated values
            _mm256_storeu_ps(temp, vc)
            sum = temp[0] + temp[1] + temp[2] + temp[3] + \
                  temp[4] + temp[5] + temp[6] + temp[7]
            
            # Handle remaining elements (if K is not divisible by 8)
            for k in range(k_block, K):
                sum += A[i, k] * BT[j, k]
            
            C[i, j] = sum
    
    return C

def add_avx2(np.ndarray[np.float32_t, ndim=1] a, 
             np.ndarray[np.float32_t, ndim=1] b):
    """
    AVX2-accelerated element-wise addition: c = a + b
    
    Parameters:
    -----------
    a, b : numpy.ndarray (N,) float32
    
    Returns:
    --------
    c : numpy.ndarray (N,) float32
    """
    if a.shape[0] != b.shape[0]:
        raise ValueError("Incompatible shapes: (%d,) vs (%d,)" % (a.shape[0], b.shape[0]))
    
    cdef int n = a.shape[0]
    cdef np.ndarray[np.float32_t, ndim=1] c = np.empty(n, dtype=np.float32)
    cdef int i
    cdef __m256 va, vb, vc
    cdef int n_block
    
    # Process 8 elements at a time
    n_block = (n // 8) * 8
    for i in range(0, n_block, 8):
        va = _mm256_loadu_ps(&a[i])
        vb = _mm256_loadu_ps(&b[i])
        vc = _mm256_add_ps(va, vb)
        _mm256_storeu_ps(&c[i], vc)
    
    # Handle remaining elements
    for i in range(n_block, n):
        c[i] = a[i] + b[i]
    
    return c

def mul_avx2(np.ndarray[np.float32_t, ndim=1] a, 
             np.ndarray[np.float32_t, ndim=1] b):
    """
    AVX2-accelerated element-wise multiplication: c = a * b
    
    Parameters:
    -----------
    a, b : numpy.ndarray (N,) float32
    
    Returns:
    --------
    c : numpy.ndarray (N,) float32
    """
    if a.shape[0] != b.shape[0]:
        raise ValueError("Incompatible shapes: (%d,) vs (%d,)" % (a.shape[0], b.shape[0]))
    
    cdef int n = a.shape[0]
    cdef np.ndarray[np.float32_t, ndim=1] c = np.empty(n, dtype=np.float32)
    cdef int i
    cdef __m256 va, vb, vc
    cdef int n_block
    
    # Process 8 elements at a time
    n_block = (n // 8) * 8
    for i in range(0, n_block, 8):
        va = _mm256_loadu_ps(&a[i])
        vb = _mm256_loadu_ps(&b[i])
        vc = _mm256_mul_ps(va, vb)
        _mm256_storeu_ps(&c[i], vc)
    
    # Handle remaining elements
    for i in range(n_block, n):
        c[i] = a[i] * b[i]
    
    return c

def dot_avx2(np.ndarray[np.float32_t, ndim=1] a, 
             np.ndarray[np.float32_t, ndim=1] b):
    """
    AVX2-accelerated dot product: result = sum(a * b)
    
    Parameters:
    -----------
    a, b : numpy.ndarray (N,) float32
    
    Returns:
    --------
    result : float
    """
    if a.shape[0] != b.shape[0]:
        raise ValueError("Incompatible shapes: (%d,) vs (%d,)" % (a.shape[0], b.shape[0]))
    
    cdef int n = a.shape[0]
    cdef int i
    cdef __m256 va, vb, vc
    cdef float temp[8]
    cdef float result = 0.0
    cdef int n_block
    
    vc = _mm256_setzero_ps()
    
    # Process 8 elements at a time
    n_block = (n // 8) * 8
    for i in range(0, n_block, 8):
        va = _mm256_loadu_ps(&a[i])
        vb = _mm256_loadu_ps(&b[i])
        vc = _mm256_fmadd_ps(va, vb, vc)
    
    # Horizontal sum
    _mm256_storeu_ps(temp, vc)
    result = temp[0] + temp[1] + temp[2] + temp[3] + \
             temp[4] + temp[5] + temp[6] + temp[7]
    
    # Handle remaining elements
    for i in range(n_block, n):
        result += a[i] * b[i]
    
    return result
