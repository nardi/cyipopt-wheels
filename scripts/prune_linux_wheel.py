"""Removes the bundled libraries of an unpacked Linux wheel that the loader never reaches.

The JLL tarballs hold more libraries than cyipopt loads, such as the MUMPS builds for other
precisions. The script starts from the libraries that the package loads (libipopt, OpenBLAS and
libblastrampoline) and follows their NEEDED entries. It removes the NEEDED entries of the
extension module for every other bundled library, and deletes the libraries that stay
unreached. The argument is the directory that `wheel unpack` wrote.
"""

import pathlib
import subprocess
import sys

from elftools.elf.elffile import ELFFile

LIBRARY_DIRECTORY_NAME = ".cyipopt.mesonpy.libs"
ROOT_PREFIXES = ("libipopt.so", "libopenblas", "libblastrampoline")
"""File name prefixes of the libraries that the package loads directly."""


def needed_names(binary_path: pathlib.Path) -> list[str]:
    """Returns the NEEDED entries of an ELF file, which are the file names the loader asks for."""
    with binary_path.open("rb") as binary_file:
        elf_file = ELFFile(binary_file)
        dynamic_section = elf_file.get_section_by_name(".dynamic")
        if dynamic_section is None:
            return []
        return [
            tag.needed
            for tag in dynamic_section.iter_tags()
            if tag.entry.d_tag == "DT_NEEDED"
        ]


def main() -> None:
    """Prunes the wheel that the first argument names."""
    wheel_directory = pathlib.Path(sys.argv[1])
    library_directory = wheel_directory / LIBRARY_DIRECTORY_NAME
    bundled_libraries = {
        path.name: path for path in library_directory.iterdir() if path.is_file()
    }
    extension_modules = sorted(wheel_directory.glob("cyipopt/*.so"))
    if not extension_modules:
        raise SystemExit(f"No extension module in `{wheel_directory}`.")

    reached = {name for name in bundled_libraries if name.startswith(ROOT_PREFIXES)}
    pending = [bundled_libraries[name] for name in reached]
    while pending:
        for dependency_name in needed_names(pending.pop()):
            if dependency_name in bundled_libraries and dependency_name not in reached:
                reached.add(dependency_name)
                pending.append(bundled_libraries[dependency_name])

    for extension_module in extension_modules:
        for dependency_name in needed_names(extension_module):
            if dependency_name in bundled_libraries and dependency_name not in reached:
                print(f"Dropping {dependency_name} from {extension_module.name}.")
                subprocess.run(
                    ["patchelf", "--remove-needed", dependency_name, str(extension_module)],
                    check=True,
                )

    for name, path in sorted(bundled_libraries.items()):
        if name not in reached:
            print(f"Removing {name}.")
            path.unlink()


if __name__ == "__main__":
    main()
