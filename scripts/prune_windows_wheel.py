"""Removes the bundled DLLs of an unpacked Windows wheel that the loader never reaches.

The DLLs of the JLL tarballs include the MUMPS builds for other precisions and the extra METIS
builds. The script starts from the DLLs that the package loads (libipopt, OpenBLAS and
libblastrampoline) and follows their import tables. It removes the imports of the extension module
for every other bundled DLL, writes the extension module back, and deletes the DLLs that stay
unreached. The argument is the directory that `wheel unpack` wrote.
"""

import pathlib
import sys

import lief

LIBRARY_DIRECTORY_NAME = ".cyipopt.mesonpy.libs"
ROOT_PREFIXES = ("libipopt-", "libopenblas", "libblastrampoline")
"""Lower case name prefixes of the DLLs that the package loads directly."""


def imported_names(binary_path: pathlib.Path) -> list[str]:
    """Returns the DLL names of the import table of a PE file, as the file spells them."""
    binary = lief.PE.parse(str(binary_path))
    if binary is None:
        raise SystemExit(f"Could not parse `{binary_path}`.")
    return [entry.name for entry in binary.imports]


def main() -> None:
    """Prunes the wheel that the first argument names."""
    wheel_directory = pathlib.Path(sys.argv[1])
    library_directory = wheel_directory / LIBRARY_DIRECTORY_NAME
    bundled_libraries = {
        path.name.lower(): path for path in library_directory.iterdir() if path.is_file()
    }
    extension_modules = sorted(wheel_directory.glob("cyipopt/*.pyd"))
    if not extension_modules:
        raise SystemExit(f"No extension module in `{wheel_directory}`.")

    # Windows file names do not depend on case, so every name is compared in lower case.
    reached = {name for name in bundled_libraries if name.startswith(ROOT_PREFIXES)}
    pending = list(reached)
    while pending:
        for dependency_name in imported_names(bundled_libraries[pending.pop()]):
            lower_name = dependency_name.lower()
            if lower_name in bundled_libraries and lower_name not in reached:
                reached.add(lower_name)
                pending.append(lower_name)

    for extension_module in extension_modules:
        binary = lief.PE.parse(str(extension_module))
        if binary is None:
            raise SystemExit(f"Could not parse `{extension_module}`.")
        for dependency_name in imported_names(extension_module):
            if dependency_name.lower() in bundled_libraries and dependency_name.lower() not in reached:
                print(f"Dropping {dependency_name} from {extension_module.name}.")
                binary.remove_import(dependency_name)
        binary.write(str(extension_module))

    for name, path in sorted(bundled_libraries.items()):
        if name not in reached:
            print(f"Removing {path.name}.")
            path.unlink()


if __name__ == "__main__":
    main()
