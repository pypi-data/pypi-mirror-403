import os
import sys
import subprocess
import glob
import sysconfig
import shutil
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# --- VERSION 4.1.0 ---
VERSION = "4.1.0"

# --- DETECTOR UTILITIES ---
def get_nvcc_path():
    p = shutil.which("nvcc")
    if p: return p
    for path in ["/usr/local/cuda/bin/nvcc", "/usr/bin/nvcc"]:
        if os.path.exists(path): return path
    return None

def check_binary(binary_name):
    try:
        if binary_name == "nvcc":
            path = get_nvcc_path()
            return path is not None
        subprocess.check_output([binary_name, "--version"], stderr=subprocess.STDOUT)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False

HAS_NVCC = check_binary("nvcc")
HAS_HIPCC = check_binary("hipcc")
FORCE_ROCM = os.environ.get("CRAYON_FORCE_ROCM") == "1"
FORCE_CUDA = os.environ.get("CRAYON_FORCE_CUDA") == "1"

# --- PURE ENGINEERING CUDA COMPILATION ---
def compile_cuda_kernel(source_file, build_dir):
    """
    Manually compile a .cu file to an object file using nvcc.
    No catch blocks here - let it fail the build if incorrect.
    """
    source_file = os.path.abspath(source_file)
    obj_name = os.path.basename(source_file).replace(".cu", ".o" if sys.platform != "win32" else ".obj")
    output_file = os.path.join(os.path.abspath(build_dir), obj_name)
    
    if not os.path.exists(build_dir):
        os.makedirs(build_dir, exist_ok=True)
    
    # Discovery of Python Includes
    includes = [
        sysconfig.get_path("include"),
        sysconfig.get_config_var('INCLUDEPY'),
        "/usr/local/cuda/include"
    ]
    include_flags = [f"-I{i}" for i in includes if i and os.path.exists(i)]
    
    nvcc_bin = get_nvcc_path() or "nvcc"
    print(f"\n[ENGINEERING] Compiling CUDA: {nvcc_bin}")
    
    # sm_75 is the T4 architecture. We target it specifically on Linux for stability.
    # We use -Xcompiler -fPIC to allow the .o to be linked into a .so extension.
    flags = ["-O3", "-c", "-std=c++14"]
    if sys.platform != "win32":
        flags.extend(["-Xcompiler", "-fPIC"])
        # If on Linux, we add architecture targeting if possible
        # flags.extend(["-arch=sm_75"]) 

    cmd = [nvcc_bin, source_file, "-o", output_file] + flags + include_flags
    
    print(f"[ENGINEERING] Command: {' '.join(cmd)}")
    
    # We do NOT capture output so it prints directly to the user's terminal
    subprocess.check_call(cmd)
    return output_file

# --- CUSTOM BUILDER ---
class CustomBuildExt(build_ext):
    def build_extensions(self):
        # Handle CUDA extension manually
        if HAS_NVCC or FORCE_CUDA:
            cuda_src = os.path.join("src", "crayon", "c_ext", "gpu_engine_cuda.cu")
            if os.path.exists(cuda_src):
                print(f"[ENGINEERING] Found CUDA source: {cuda_src}")
                os.makedirs(self.build_temp, exist_ok=True)
                
                # If this fails, the whole setuptools build fails (Loudly)
                obj_path = compile_cuda_kernel(cuda_src, self.build_temp)
                
                for ext in self.extensions:
                    if "crayon_cuda" in ext.name:
                        # Replace the .cu source with the compiled .o object
                        ext.sources = [s for s in ext.sources if not s.endswith(".cu")]
                        ext.extra_objects.append(obj_path)
            else:
                 print(f"[ENGINEERING] ERROR: CUDA source missing at {cuda_src}")
        
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
if HAS_NVCC or FORCE_CUDA:
    cuda_lib_dirs = ["/usr/local/cuda/lib64", "/usr/local/cuda/lib"] if sys.platform != "win32" else []
    
    ext_modules.append(Extension(
        "crayon.c_ext.crayon_cuda",
        sources=["src/crayon/c_ext/gpu_engine_cuda.cu"], # Keep for awareness
        libraries=["cudart"],
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