import os
import sys
import subprocess
import glob
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# --- VERSION ---
VERSION = "4.0.4"

# --- DETECTOR UTILITIES ---
def check_binary(binary_name):
    try:
        subprocess.check_output([binary_name, "--version"], stderr=subprocess.STDOUT)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False

HAS_NVCC = check_binary("nvcc")
HAS_HIPCC = check_binary("hipcc")
FORCE_ROCM = os.environ.get("CRAYON_FORCE_ROCM") == "1"
FORCE_CUDA = os.environ.get("CRAYON_FORCE_CUDA") == "1"

# --- MANUAL COMPILATION HELPER ---
def compile_cuda_kernel(source_file):
    """
    Manually compile a .cu file to an object file using nvcc.
    Returns the path to the compiled object file.
    """
    # Define output filename (e.g. src/crayon/c_ext/gpu_engine_cuda.obj)
    obj_ext = ".obj" if sys.platform == "win32" else ".o"
    output_file = os.path.splitext(source_file)[0] + obj_ext
    
    print(f"[CRAYON BUILD] Compiling {source_file} -> {output_file} via NVCC...")
    
    # Flags
    flags = ["-O3", "-c", "--compiler-options", "-fPIC"]
    if sys.platform == "win32":
        flags = ["-O3", "-c"] # Windows doesn't need fPIC usually, and handles compiler output differently

    # Command: nvcc input -o output flags
    cmd = ["nvcc", source_file, "-o", output_file] + flags
    
    try:
        subprocess.check_call(cmd)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"[!] NVCC Compilation Failed: {e}")
        return None

# --- CUSTOM BUILDER ---
class CustomBuildExt(build_ext):
    def build_extensions(self):
        # 1. Compile CUDA source manually if NVCC is available
        # This bypasses setuptools attempting to use GCC for .cu files
        if HAS_NVCC or FORCE_CUDA:
            cuda_src = "src/crayon/c_ext/gpu_engine_cuda.cu"
            if os.path.exists(cuda_src):
                obj_path = compile_cuda_kernel(cuda_src)
                if obj_path:
                    # Find the crayon_cuda extension and add the object
                    for ext in self.extensions:
                        if ext.name == "crayon.c_ext.crayon_cuda":
                            # We REMOVE the .cu source so setuptools doesn't try to compile it again
                            ext.sources = [s for s in ext.sources if not s.endswith(".cu")]
                            # We add the compiled object file to link against
                            ext.extra_objects.append(obj_path)
        
        # 2. Proceed with standard build
        super().build_extensions()

ext_modules = []

# --- 1. CPU BACKEND ---
cpu_flags = ["-O3", "-fPIC"]
if sys.platform == "linux" or sys.platform == "darwin":
    cpu_flags += ["-march=native", "-mavx512f", "-mavx512bw"]
elif sys.platform == "win32":
    cpu_flags = ["/O2", "/arch:AVX2"]

ext_modules.append(Extension(
    "crayon.c_ext.crayon_cpu",
    sources=["src/crayon/c_ext/cpu_engine.cpp"],
    extra_compile_args=cpu_flags,
    language="c++"
))

# --- 2. CUDA BACKEND ---
if HAS_NVCC or FORCE_CUDA:
    # Note: We list the .cu source here initially so it's tracked,
    # but CustomBuildExt will remove it and replace it with the .o file.
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_cuda",
        sources=["src/crayon/c_ext/gpu_engine_cuda.cu"], 
        libraries=["cudart"] if sys.platform == "win32" else [],
        extra_objects=[], # Will be populated by CustomBuildExt
    ))

# --- 3. ROCM BACKEND ---
if HAS_HIPCC or FORCE_ROCM:
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_rocm",
        sources=["src/crayon/c_ext/rocm_engine.cpp"],
        extra_compile_args=["-D__HIP_PLATFORM_AMD__"],
        libraries=["amdhip64"],
    ))

# --- SETUP ---
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="xerv-crayon",
    version=VERSION,
    description="The Omni-Backend Tokenizer (CPU/CUDA/ROCm)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Xerv-AI/crayon",
    author="Xerv Research Engineering Division",
    author_email="botmaker583@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    ext_modules=ext_modules,
    cmdclass={'build_ext': CustomBuildExt},
    python_requires=">=3.10",
)