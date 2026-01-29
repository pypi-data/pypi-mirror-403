from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import sys
import platform

# Check for AVX2 support
def check_avx2_support():
    if platform.machine() not in ['x86_64', 'AMD64']:
        print("Warning: AVX2 requires x86_64 architecture")
        return False
    return True

if not check_avx2_support():
    print("Building without AVX2 optimizations")
    extra_compile_args = []
else:
    if sys.platform == 'win32':
        extra_compile_args = ['/arch:AVX2', '/O2']
    else:
        # -mfma is required for FMA instructions (fused multiply-add)
        extra_compile_args = ['-mavx2', '-mfma', '-O3', '-ffast-math']

extensions = [
    Extension(
        "pyVX2.avx2_ops",
        sources=["pyVX2/avx2_ops.pyx"],
        extra_compile_args=extra_compile_args,
        include_dirs=[np.get_include()],
        language="c",
    )
]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyvx2-sbhadade",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AVX2-accelerated array and matrix operations for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyVX2",
    packages=["pyVX2"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Cython",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
    ],
    ext_modules=cythonize(extensions, compiler_directives={
        'language_level': "3",
        'boundscheck': False,
        'wraparound': False,
    }),
    zip_safe=False,
)
