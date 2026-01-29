"""PyVX2 - AVX2 Accelerated Array Operations for Python"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .avx2_ops import matmul_avx2, add_avx2, mul_avx2, dot_avx2

__all__ = ['matmul_avx2', 'add_avx2', 'mul_avx2', 'dot_avx2']
