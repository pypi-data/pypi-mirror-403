import os
import sys
import subprocess
from setuptools import setup, Extension, find_packages

# --- DETECTOR UTILITIES ---
def check_binary(binary_name):
    """
    Checks if a compiler binary exists in the system PATH.
    Returns True if found, False otherwise.
    """
    try:
        # Run with --version to verify it's executable
        subprocess.check_output([binary_name, "--version"], stderr=subprocess.STDOUT)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False

# Detect Hardware Compilers via shell
HAS_NVCC = check_binary("nvcc")
HAS_HIPCC = check_binary("hipcc")
# Allow forced overrides via environment variables for CI/CD pipelines
FORCE_ROCM = os.environ.get("CRAYON_FORCE_ROCM") == "1"
FORCE_CUDA = os.environ.get("CRAYON_FORCE_CUDA") == "1"

ext_modules = []

# --- 1. CPU BACKEND (The Foundation) ---
# Supports AVX2 (Standard) and AVX-512 (Nitro)
cpu_flags = ["-O3", "-fPIC"]
if sys.platform == "linux" or sys.platform == "darwin":
    cpu_flags.append("-march=native") # Optimize for the build machine's CPU
    # Explicitly enable AVX512 support in compiler so intrinsics code compiles
    cpu_flags.append("-mavx512f") 
    cpu_flags.append("-mavx512bw")
elif sys.platform == "win32":
    # MSVC specific flags
    cpu_flags = ["/O2", "/arch:AVX2"] 

ext_modules.append(Extension(
    "crayon.c_ext.crayon_cpu",
    sources=["src/crayon/c_ext/cpu_engine.cpp"],
    extra_compile_args=cpu_flags,
    language="c++"
))

# --- 2. NVIDIA CUDA BACKEND (Green Team) ---
from setuptools.command.build_ext import build_ext

# --- CUSTOM BUILD EXTENSION FOR CUDA ---
class CUDA_BuildExt(build_ext):
    """
    Custom build_ext command that compiles .cu files using nvcc.
    """
    def build_extensions(self):
        # Identify CUDA extensions
        cuda_exts = [ext for ext in self.extensions if any(s.endswith(".cu") for s in ext.sources)]
        
        for ext in cuda_exts:
            # Add nvcc flags
            ext.extra_compile_args = {"cxx": [], "nvcc": ["-O3", "--ptxas-options=-v", "-c", "--compiler-options", "'-fPIC'"]}
            
            # If on Windows, we need specific MSVC flags passed through nvcc
            if sys.platform == "win32":
                 ext.extra_compile_args["nvcc"] = ["-O3", "-c"]

        # Run standard build
        super().build_extensions()

# --- 2. NVIDIA CUDA BACKEND (Green Team) ---
if HAS_NVCC or FORCE_CUDA:
    print("[+] [CRAYON BUILD] NVIDIA NVCC detected. Building 'crayon_cuda'...")
    
    cuda_ext = Extension(
        "crayon.c_ext.crayon_cuda",
        sources=["src/crayon/c_ext/gpu_engine_cuda.cu"],
        # We leave libraries empty for Linux/Colab; let nvcc handle linking or use environment vars.
        # On Windows, setup.py usually finds cudart if CUDA_PATH is set.
        libraries=["cudart"] if sys.platform == "win32" else [],
    )
    ext_modules.append(cuda_ext)
else:
    print("[!] [CRAYON BUILD] NVCC not found. Skipping NVIDIA Backend.")

# --- 3. AMD ROCm BACKEND (Red Team) ---
if HAS_HIPCC or FORCE_ROCM:
    print("[+] [CRAYON BUILD] AMD HIPCC detected. Building 'crayon_rocm'...")
    
    # HIPCC acts like GCC/Clang but links ROCm runtime automatically when invoked.
    # We define the macro so the preprocessor knows we are on AMD.
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_rocm",
        sources=["src/crayon/c_ext/rocm_engine.cpp"],
        extra_compile_args=["-D__HIP_PLATFORM_AMD__"],
        # Link against the HIP runtime library
        libraries=["amdhip64"], 
    ))
else:
    print("[!] [CRAYON BUILD] HIPCC not found. Skipping AMD Backend.")

# Read README for PyPI long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="xerv-crayon",
    version="4.0.3",
    description="The Omni-Backend Tokenizer (CPU/CUDA/ROCm)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Xerv-AI/crayon",
    author="Xerv Research Engineering Division",
    author_email="botmaker583@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    ext_modules=ext_modules,
    # Inject our custom build_ext to handle CUDA
    cmdclass={'build_ext': CUDA_BuildExt},
    python_requires=">=3.10",
)