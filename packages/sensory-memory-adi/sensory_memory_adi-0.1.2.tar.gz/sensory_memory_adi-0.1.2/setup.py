import os
from setuptools import setup, Extension

def build_ext_modules():
    if os.environ.get("SENSORY_MEMORY_ADI_BUILD_EXT", "").strip() != "1":
        return []
    try:
        import pybind11
    except Exception as e:
        raise RuntimeError("pybind11 is required. Install with sensory-memory-adi[speed].") from e

    return [
        Extension(
            "sensory_memory_adi.ext._fast_ring",
            ["sensory_memory_adi/ext/_fast_ring.cpp"],
            include_dirs=[pybind11.get_include()],
            language="c++",
            extra_compile_args=["-O3"],
        )
    ]

setup(ext_modules=build_ext_modules())
