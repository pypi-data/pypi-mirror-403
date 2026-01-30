import os
import sys
import subprocess
import glob
import sysconfig
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

import shutil

# --- VERSION ---
VERSION = "4.0.9"

# --- DETECTOR UTILITIES ---
def get_nvcc_path():
    p = shutil.which("nvcc")
    if p: return p
    # Common Linux locations
    for path in ["/usr/local/cuda/bin/nvcc", "/usr/bin/nvcc"]:
        if os.path.exists(path): return path
    return None

def check_binary(binary_name):
    try:
        if binary_name == "nvcc":
            path = get_nvcc_path()
            if not path: return False
            subprocess.check_output([path, "--version"], stderr=subprocess.STDOUT)
            return True
        subprocess.check_output([binary_name, "--version"], stderr=subprocess.STDOUT)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False

HAS_NVCC = check_binary("nvcc")
HAS_HIPCC = check_binary("hipcc")
FORCE_ROCM = os.environ.get("CRAYON_FORCE_ROCM") == "1"
FORCE_CUDA = os.environ.get("CRAYON_FORCE_CUDA") == "1"

# --- MANUAL COMPILATION HELPER ---
def compile_cuda_kernel(source_file, build_dir):
    """
    Manually compile a .cu file to an object file using nvcc.
    """
    source_file = os.path.abspath(source_file)
    obj_name = os.path.basename(source_file).replace(".cu", ".o" if sys.platform != "win32" else ".obj")
    output_file = os.path.join(build_dir, obj_name)
    
    if not os.path.exists(build_dir):
        os.makedirs(build_dir, exist_ok=True)
    
    # Comprehensive Include Discovery
    includes = [
        sysconfig.get_path("include"),
        sysconfig.get_config_var('INCLUDEPY'),
        sysconfig.get_config_var('CONFINCLUDEPY'),
        "/usr/local/cuda/include"
    ]
    # Filter and format
    includes = [f"-I{i}" for i in includes if i and os.path.exists(i)]
    
    nvcc_bin = get_nvcc_path() or "nvcc"
    print(f"[CRAYON BUILD] {nvcc_bin} compiling: {source_file} -> {output_file}")
    
    # Flags: Optimized for modern NVIDIA hardware (Colab T4 = sm_75)
    flags = ["-O3", "-c", "-std=c++14"] # c++14 is extremely stable for NVCC
    if sys.platform != "win32":
        flags.extend(["-Xcompiler", "-fPIC"])

    cmd = [nvcc_bin, source_file, "-o", output_file] + flags + includes
    
    try:
        print(f"[CRAYON EXEC] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("\n" + "="*40)
            print("❌ NVCC COMPILATION FAILED")
            print("="*40)
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print("="*40)
            raise RuntimeError(f"NVCC failed with return code {result.returncode}")
        return output_file
    except Exception as e:
        print(f"[!] NVCC Invocation Fatal Error: {e}")
        raise

# --- CUSTOM BUILDER ---
class CustomBuildExt(build_ext):
    def build_extensions(self):
        # 1. Handle CUDA
        if HAS_NVCC or FORCE_CUDA:
            cuda_src = os.path.join("src", "crayon", "c_ext", "gpu_engine_cuda.cu")
            if os.path.exists(cuda_src):
                # Ensure build_temp exists
                os.makedirs(self.build_temp, exist_ok=True)
                try:
                    obj_path = compile_cuda_kernel(cuda_src, self.build_temp)
                    if obj_path:
                        for ext in self.extensions:
                            if "crayon_cuda" in ext.name:
                                # REMOVE THE SOURCE so setuptools doesn't try to compile it with gcc
                                ext.sources = [s for s in ext.sources if not s.endswith(".cu")]
                                ext.extra_objects.append(obj_path)
                                print(f"[CRAYON BUILD] Successfully linked {obj_path} into extension.")
                except Exception as e:
                    print(f"[CRAYON BUILD] CUDA build failed. Skipping extension: {e}")
                    # Remove the extension so the rest of the package installs (CPU only fallback)
                    self.extensions = [ext for ext in self.extensions if "crayon_cuda" not in ext.name]
            else:
                 print(f"[!] Source not found: {cuda_src}")
        
        # 2. Standard Build
        super().build_extensions()

ext_modules = []

# --- 1. CPU BACKEND ---
cpu_flags = ["-O3", "-fPIC"]
if sys.platform == "linux" or sys.platform == "darwin":
    cpu_flags += ["-march=native"]
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
    cuda_lib_dirs = ["/usr/local/cuda/lib64", "/usr/local/cuda/lib"] if sys.platform != "win32" else []
    cuda_libs = ["cudart"]
    
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_cuda",
        sources=["src/crayon/c_ext/gpu_engine_cuda.cu"], 
        libraries=cuda_libs,
        library_dirs=cuda_lib_dirs,
        runtime_library_dirs=cuda_lib_dirs if sys.platform != "win32" else [],
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