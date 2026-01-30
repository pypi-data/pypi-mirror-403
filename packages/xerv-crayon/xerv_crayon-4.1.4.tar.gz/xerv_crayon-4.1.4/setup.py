import os
import sys
import subprocess
import glob
import sysconfig
import shutil
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# --- VERSION 4.1.4 ---
VERSION = "4.1.4"

def get_nvcc_path():
    p = shutil.which("nvcc")
    if p: return p
    for path in ["/usr/local/cuda/bin/nvcc", "/usr/bin/nvcc", "/usr/local/cuda-12/bin/nvcc", "/usr/local/cuda-11/bin/nvcc"]:
        if os.path.exists(path): return path
    return None

NVCC_BIN = get_nvcc_path()
HAS_NVCC = NVCC_BIN is not None

def compile_cuda_kernel(source_file, build_dir):
    source_file = os.path.abspath(source_file)
    obj_name = os.path.basename(source_file).replace(".cu", ".o" if sys.platform != "win32" else ".obj")
    output_file = os.path.join(os.path.abspath(build_dir), obj_name)
    
    if not os.path.exists(build_dir): os.makedirs(build_dir, exist_ok=True)
    
    includes = [sysconfig.get_path("include"), sysconfig.get_config_var('INCLUDEPY'), "/usr/local/cuda/include"]
    include_flags = [f"-I{i}" for i in includes if i and os.path.exists(i)]
    
    # Targeting T4 (75), A100 (80), H100 (90)
    flags = ["-O3", "-c", "-std=c++11"]
    if sys.platform != "win32":
        flags.extend(["-Xcompiler", "-fPIC"])
        # Multi-Architecture Support
        flags.extend(["-gencode", "arch=compute_75,code=sm_75"]) # T4
        flags.extend(["-gencode", "arch=compute_80,code=sm_80"]) # A100
        flags.extend(["-gencode", "arch=compute_90,code=sm_90"]) # H100/H200

    cmd = [NVCC_BIN, source_file, "-o", output_file] + flags + include_flags
    print(f"[CRAYON] NVCC: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    return output_file

class CustomBuildExt(build_ext):
    def build_extensions(self):
        if HAS_NVCC:
            cuda_src = os.path.join("src", "crayon", "c_ext", "gpu_engine_cuda.cu")
            if os.path.exists(cuda_src):
                os.makedirs(self.build_temp, exist_ok=True)
                obj_path = compile_cuda_kernel(cuda_src, self.build_temp)
                for ext in self.extensions:
                    if "crayon_cuda" in ext.name:
                        # Merge the CUDA object and the C module
                        ext.extra_objects.append(obj_path)
            else:
                 print(f"[CRAYON] Error: CUDA file missing at {cuda_src}")
        super().build_extensions()

ext_modules = []
# CPU Extension
ext_modules.append(Extension(
    "crayon.c_ext.crayon_cpu",
    sources=["src/crayon/c_ext/cpu_engine.cpp"],
    extra_compile_args=["-O3", "-fPIC", "-march=native"] if sys.platform != "win32" else ["/O2", "/arch:AVX2"],
    language="c++"
))

# CUDA Extension (Initialized with module shell)
if HAS_NVCC:
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_cuda",
        sources=["src/crayon/c_ext/crayon_module.c"],
        libraries=["cudart"],
        library_dirs=["/usr/local/cuda/lib64", "/usr/local/cuda/lib"] if sys.platform != "win32" else [],
        runtime_library_dirs=["/usr/local/cuda/lib64"] if sys.platform != "win32" else [],
    ))

setup(
    name="xerv-crayon",
    version=VERSION,
    description="The Omni-Backend Tokenizer",
    long_description="High-Speed Tokenization Engine",
    author="Xerv Research",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={"crayon.resources.dat": ["*.dat", "*.json"]},
    ext_modules=ext_modules,
    cmdclass={'build_ext': CustomBuildExt},
    python_requires=">=3.10",
)