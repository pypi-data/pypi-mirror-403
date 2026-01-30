import os
import sys
import subprocess
import shutil
import sysconfig
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# --- VERSION 4.1.7 ---
VERSION = "4.1.7"

def get_nvcc_path():
    p = shutil.which("nvcc")
    if p: return p
    for path in ["/usr/local/cuda/bin/nvcc", "/usr/bin/nvcc", "/usr/local/cuda-12/bin/nvcc"]:
        if os.path.exists(path): return path
    return None

NVCC_BIN = get_nvcc_path()
HAS_NVCC = NVCC_BIN is not None

def compile_cuda_kernel(source_file, build_dir):
    source_file = os.path.abspath(source_file)
    obj_name = os.path.basename(source_file).replace(".cu", ".o" if sys.platform != "win32" else ".obj")
    output_file = os.path.join(os.path.abspath(build_dir), obj_name)
    
    if not os.path.exists(build_dir): os.makedirs(build_dir, exist_ok=True)
    
    # Discovery of Python Includes
    includes = [
        sysconfig.get_path("include"),
        sysconfig.get_config_var('INCLUDEPY'),
        sysconfig.get_config_var('CONFINCLUDEPY'),
        "/usr/local/cuda/include"
    ]
    include_flags = [f"-I{i}" for i in includes if i and os.path.exists(i)]
    
    # Flags for T4, A100, H100
    # FIX: Upgrade to C++17 for modern Python 3.12 compatibility
    flags = ["-O3", "-c", "-std=c++17"] 
    if sys.platform != "win32":
        flags.extend(["-Xcompiler", "-fPIC"])
        # Use simple architecture targeting that works on almost all CUDA versions
        flags.extend(["-gencode", "arch=compute_75,code=sm_75"])
        flags.extend(["-gencode", "arch=compute_80,code=sm_80"])

    cmd = [NVCC_BIN, source_file, "-o", output_file] + flags + include_flags
    print(f"[CRAYON] NVCC: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    return output_file

class CustomBuildExt(build_ext):
    def build_extensions(self):
        if HAS_NVCC:
            cuda_src = os.path.join("src", "crayon", "c_ext", "gpu_engine_cuda.cu")
            if os.path.exists(cuda_src):
                print("[CRAYON] Compiling CUDA Kernels...")
                os.makedirs(self.build_temp, exist_ok=True)
                obj_path = compile_cuda_kernel(cuda_src, self.build_temp)
                for ext in self.extensions:
                    if "crayon_cuda" in ext.name:
                        ext.extra_objects.append(obj_path)
            else:
                 print(f"[CRAYON] Warning: CUDA file missing at {cuda_src}")
        super().build_extensions()

ext_modules = []

# 1. CPU Backend
ext_modules.append(Extension(
    "crayon.c_ext.crayon_cpu",
    sources=["src/crayon/c_ext/cpu_engine.cpp"],
    extra_compile_args=["-O3", "-fPIC", "-march=native"] if sys.platform != "win32" else ["/O2", "/arch:AVX2"],
    language="c++"
))

# 2. CUDA Backend
if HAS_NVCC:
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_cuda",
        sources=["src/crayon/c_ext/gpu_engine_cuda.cu"], # Let setuptools know about dependency
        libraries=["cudart"],
        library_dirs=["/usr/local/cuda/lib64", "/usr/local/cuda/lib"] if sys.platform != "win32" else [],
        runtime_library_dirs=["/usr/local/cuda/lib64"] if sys.platform != "win32" else [],
    ))

setup(
    name="xerv-crayon",
    version=VERSION,
    description="The Omni-Backend Tokenizer",
    long_description="High-Speed Universal Tokenization",
    author="Xerv Research",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={"crayon.resources.dat": ["*.dat", "*.json"]},
    ext_modules=ext_modules,
    cmdclass={'build_ext': CustomBuildExt},
    python_requires=">=3.10",
)