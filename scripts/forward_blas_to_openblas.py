"""Makes the `cyipopt/__init__.py` of an unpacked sdist forward BLAS to the bundled OpenBLAS.

Ipopt calls BLAS through libblastrampoline, which has no BLAS library of its own. Without a
forwarding call the first BLAS call crashes. The script adds the forwarding to the package, and
it also adds the directory of the bundled DLLs to the DLL search path on Windows, before the
extension module loads. The script takes the path of the `__init__.py` file.
"""

import pathlib
import sys

DLL_DIRECTORY_CODE = '''import os as _os
import sys as _sys

if _sys.platform == "win32":
    _bundled_directory = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        ".cyipopt.mesonpy.libs",
    )
    if _os.path.isdir(_bundled_directory):
        _os.add_dll_directory(_bundled_directory)


'''

FORWARDING_CODE = '''

import ctypes
import glob
import os


def _find_bundled_library(name_prefix):
    """Returns the bundled library whose file name starts with `name_prefix`."""
    package_directory = os.path.dirname(os.path.abspath(__file__))
    site_directory = os.path.dirname(package_directory)
    # meson-python puts the libraries next to the package, auditwheel and delvewheel into
    # `cyipopt.libs`, and delocate into `cyipopt/.dylibs`.
    candidate_directories = [
        os.path.join(site_directory, ".cyipopt.mesonpy.libs"),
        os.path.join(site_directory, "cyipopt.libs"),
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
    if forward(openblas_path.encode(), 1, 0, None) == 0:
        raise ImportError(f"libblastrampoline could not forward to `{openblas_path}`.")


_forward_blas_to_openblas()
'''

IMPORT_LINE = "from .ipopt_wrapper import *"


def main() -> None:
    """Rewrites the package file that the first argument names."""
    init_path = pathlib.Path(sys.argv[1])
    original_text = init_path.read_text(encoding="utf-8")
    if original_text.count(IMPORT_LINE) != 1:
        raise SystemExit(f"The line `{IMPORT_LINE}` is missing from `{init_path}`.")
    # The DLL search path is set before the extension module imports its libraries.
    rewritten_text = original_text.replace(
        IMPORT_LINE, DLL_DIRECTORY_CODE + IMPORT_LINE, 1
    )
    init_path.write_text(rewritten_text + FORWARDING_CODE, encoding="utf-8")


if __name__ == "__main__":
    main()
