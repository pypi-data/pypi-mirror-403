import os
import sys
import subprocess
import glob
import sysconfig
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# --- VERSION ---
VERSION = "4.0.8"

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
def compile_cuda_kernel(source_file, build_dir):
    """
    Manually compile a .cu file to an object file using nvcc.
    """
    source_file = os.path.abspath(source_file)
    obj_name = os.path.basename(source_file).replace(".cu", ".o" if sys.platform != "win32" else ".obj")
    output_file = os.path.join(build_dir, obj_name)
    
    if not os.path.exists(build_dir):
        os.makedirs(build_dir, exist_ok=True)
    
    # Python & CUDA Include Paths
    includes = [
        sysconfig.get_path("include"),
        sysconfig.get_config_var('CONFINCLUDEPY'),
        "/usr/local/cuda/include" # Standard Linux path
    ]
    includes = [f"-I{i}" for i in includes if i and os.path.exists(i)]
    
    print(f"[CRAYON BUILD] NVCC compiling: {source_file} -> {output_file}")
    
    # Flags: -std=c++17, -Xcompiler -fPIC
    flags = ["-O3", "-c", "-std=c++11"] # CUDA 11/12 on Colab prefers c++11/14/17
    if sys.platform != "win32":
        flags.extend(["-Xcompiler", "-fPIC"])

    cmd = ["nvcc", source_file, "-o", output_file] + flags + includes
    
    try:
        print(f"[CRAYON EXEC] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("[!] NVCC STDOUT:", result.stdout)
            print("[!] NVCC STDERR:", result.stderr)
            return None
        return output_file
    except Exception as e:
        print(f"[!] NVCC Invocation Fatal: {e}")
        return None

# --- CUSTOM BUILDER ---
class CustomBuildExt(build_ext):
    def build_extensions(self):
        # 1. Handle CUDA
        if HAS_NVCC or FORCE_CUDA:
            cuda_src = os.path.join("src", "crayon", "c_ext", "gpu_engine_cuda.cu")
            if os.path.exists(cuda_src):
                # Ensure build_temp exists
                os.makedirs(self.build_temp, exist_ok=True)
                obj_path = compile_cuda_kernel(cuda_src, self.build_temp)
                if obj_path:
                    for ext in self.extensions:
                        if "crayon_cuda" in ext.name:
                            ext.sources = [s for s in ext.sources if not s.endswith(".cu")]
                            ext.extra_objects.append(obj_path)
                            # Ensure we don't try to use standard compiler for it
            else:
                 print(f"[!] Source not found: {cuda_src}")
        
        # 2. Standard Build
        super().build_extensions()

ext_modules = []

# --- 1. CPU BACKEND ---
cpu_flags = ["-O3", "-fPIC"]
if sys.platform == "linux" or sys.platform == "darwin":
    cpu_flags += ["-march=native"] # No hardcoded AVX-512 (safer)
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