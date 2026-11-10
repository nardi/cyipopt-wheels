"""Appends the BLAS forwarding to the `cyipopt/__init__.py` of an unpacked sdist.

Ipopt calls BLAS through libblastrampoline, which has no BLAS library of its
own. Without a forwarding call the first BLAS call crashes, so the appended
code makes libblastrampoline forward to the OpenBLAS that the repair tool
bundles into the wheel. The script takes the path of the `__init__.py` file.
"""

import pathlib
import sys

APPENDED_CODE = '''

import ctypes
import glob
import os


def _find_bundled_library(name_prefix):
    """Returns the bundled library whose file name starts with `name_prefix`."""
    package_directory = os.path.dirname(os.path.abspath(__file__))
    # auditwheel and delvewheel bundle into `cyipopt.libs`, delocate into `cyipopt/.dylibs`.
    candidate_directories = [
        os.path.join(package_directory, os.pardir, "cyipopt.libs"),
        os.path.join(package_directory, ".dylibs"),
    ]
    for candidate_directory in candidate_directories:
        matches = sorted(glob.glob(os.path.join(candidate_directory, name_prefix + "*")))
        if matches:
            return matches[0]
    raise ImportError(f"The bundled library `{name_prefix}` is missing from the wheel.")


def _forward_blas_to_openblas():
    """Forwards the BLAS and LAPACK calls of libblastrampoline to the bundled OpenBLAS."""
    blastrampoline = ctypes.CDLL(
        _find_bundled_library("libblastrampoline"), mode=ctypes.RTLD_GLOBAL
    )
    forward = blastrampoline.lbt_forward
    forward.restype = ctypes.c_int32
    forward.argtypes = [ctypes.c_char_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_char_p]
    openblas_path = _find_bundled_library("libopenblas")
    # The function returns zero when libblastrampoline cannot load the library.
    if forward(openblas_path.encode(), 0, 0, None) == 0:
        raise ImportError(f"libblastrampoline could not forward to `{openblas_path}`.")


_forward_blas_to_openblas()
'''


def main() -> None:
    """Appends the forwarding code to the file that the first argument names."""
    init_path = pathlib.Path(sys.argv[1])
    original_text = init_path.read_text(encoding="utf-8")
    init_path.write_text(original_text + APPENDED_CODE, encoding="utf-8")


if __name__ == "__main__":
    main()
