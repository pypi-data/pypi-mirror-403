import os
import sys
import subprocess
import glob
import sysconfig
import shutil
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# --- VERSION 4.1.3 ---
VERSION = "4.1.3"

# --- DETECTOR UTILITIES ---
def get_nvcc_path():
    # 1. Check PATH
    p = shutil.which("nvcc")
    if p: return p
    # 2. Check Standard Linux CUDA locations
    for path in [
        "/usr/local/cuda/bin/nvcc", 
        "/usr/bin/nvcc", 
        "/usr/local/cuda-12/bin/nvcc",
        "/usr/local/cuda-11/bin/nvcc",
        "/usr/local/cuda-12.2/bin/nvcc"
    ]:
        if os.path.exists(path): return path
    return None

NVCC_BIN = get_nvcc_path()
HAS_NVCC = NVCC_BIN is not None

print(f"\n[ENGINEERING] NVCC Detection: {NVCC_BIN if HAS_NVCC else 'NOT FOUND'}")

# --- MANUAL COMPILATION HELPER ---
def compile_cuda_kernel(source_file, build_dir):
    source_file = os.path.abspath(source_file)
    obj_name = os.path.basename(source_file).replace(".cu", ".o" if sys.platform != "win32" else ".obj")
    output_file = os.path.join(os.path.abspath(build_dir), obj_name)
    
    if not os.path.exists(build_dir):
        os.makedirs(build_dir, exist_ok=True)
    
    includes = [
        sysconfig.get_path("include"),
        sysconfig.get_config_var('INCLUDEPY'),
        "/usr/local/cuda/include"
    ]
    include_flags = [f"-I{i}" for i in includes if i and os.path.exists(i)]
    
    # Target T4 (75), A100 (80), H100 (90)
    flags = ["-O3", "-c", "-std=c++11"]
    if sys.platform != "win32":
        flags.extend(["-Xcompiler", "-fPIC"])
        flags.extend(["-gencode", "arch=compute_75,code=sm_75"])
        flags.extend(["-gencode", "arch=compute_80,code=sm_80"])
        flags.extend(["-gencode", "arch=compute_90,code=sm_90"])

    cmd = [NVCC_BIN, source_file, "-o", output_file] + flags + include_flags
    print(f"[ENGINEERING] Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    return output_file

# --- CUSTOM BUILDER ---
class CustomBuildExt(build_ext):
    def build_extensions(self):
        if HAS_NVCC:
            cuda_src = os.path.join("src", "crayon", "c_ext", "gpu_engine_cuda.cu")
            if os.path.exists(cuda_src):
                print(f"[ENGINEERING] Building CUDA Extension...")
                os.makedirs(self.build_temp, exist_ok=True)
                obj_path = compile_cuda_kernel(cuda_src, self.build_temp)
                
                for ext in self.extensions:
                    if "crayon_cuda" in ext.name:
                        ext.sources = [s for s in ext.sources if not s.endswith(".cu")]
                        # We keep one source so setuptools doesn't think the extension is empty
                        ext.sources.append(os.path.join("src", "crayon", "c_ext", "crayon_module.c"))
                        ext.extra_objects.append(obj_path)
            else:
                 print(f"[ENGINEERING] ERROR: CUDA Source missing at {cuda_src}")
        else:
            print("[ENGINEERING] WARNING: NVCC not found. GPU backend will NOT be built.")
        
        super().build_extensions()

ext_modules = []

# --- 1. CPU BACKEND ---
cpu_flags = ["-O3", "-fPIC"]
if sys.platform != "win32":
    cpu_flags += ["-march=native"]
else:
    cpu_flags = ["/O2", "/arch:AVX2"]

ext_modules.append(Extension(
    "crayon.c_ext.crayon_cpu",
    sources=["src/crayon/c_ext/cpu_engine.cpp"],
    extra_compile_args=cpu_flags,
    language="c++"
))

# --- 2. CUDA BACKEND ---
if HAS_NVCC:
    cuda_lib_dirs = ["/usr/local/cuda/lib64", "/usr/local/cuda/lib"] if sys.platform != "win32" else []
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_cuda",
        sources=[], # Will be populated by CustomBuildExt
        libraries=["cudart"],
        library_dirs=cuda_lib_dirs,
        runtime_library_dirs=cuda_lib_dirs if sys.platform != "win32" else [],
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
    author="Xerv Research Engineering Division",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={"crayon.resources.dat": ["*.dat", "*.json"]},
    ext_modules=ext_modules,
    cmdclass={'build_ext': CustomBuildExt},
    python_requires=">=3.10",
)