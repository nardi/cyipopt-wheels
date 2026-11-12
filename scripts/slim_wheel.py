"""Removes the bundled libraries that nothing loads from an unpacked wheel.

The JLL tarballs hold more libraries than cyipopt uses, such as the MUMPS builds for other
precisions. The script follows the dependencies of the extension module and of the two
libraries that the package loads by path, and deletes every bundled library that is not
reached. On macOS it also strips the local symbols of the remaining libraries and signs them
again. The first argument is the directory that `wheel unpack` wrote.
"""

import pathlib
import re
import subprocess
import sys

LIBRARY_DIRECTORY_NAME = ".cyipopt.mesonpy.libs"
LOADED_BY_PATH_PREFIXES = ("libopenblas", "libblastrampoline")
"""Name prefixes of the libraries that `cyipopt/__init__.py` loads by path."""


def dependency_names(binary_path: pathlib.Path) -> set[str]:
    """Returns the file names of the libraries that `binary_path` asks the loader for."""
    if sys.platform == "win32":
        import pefile

        portable_executable = pefile.PE(str(binary_path), fast_load=True)
        portable_executable.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        entries = getattr(portable_executable, "DIRECTORY_ENTRY_IMPORT", [])
        return {entry.dll.decode() for entry in entries}
    if sys.platform == "darwin":
        output = subprocess.run(
            ["otool", "-L", str(binary_path)], check=True, capture_output=True, text=True
        ).stdout
        # The first line names the file itself, and each other line starts with a path.
        paths = [line.split()[0] for line in output.splitlines()[1:] if line.strip()]
        return {pathlib.PurePosixPath(path).name for path in paths}
    output = subprocess.run(
        ["readelf", "-d", str(binary_path)], check=True, capture_output=True, text=True
    ).stdout
    return set(re.findall(r"\(NEEDED\).*\[(.*)\]", output))


def reachable_libraries(
    root_paths: list[pathlib.Path], bundled_libraries: dict[str, pathlib.Path]
) -> set[str]:
    """Returns the names of the bundled libraries that the roots depend on, directly or not."""
    # Windows file names are compared without regard to case.
    names_by_key = {name.lower(): name for name in bundled_libraries}
    reached: set[str] = set()
    pending = list(root_paths)
    while pending:
        for dependency_name in dependency_names(pending.pop()):
            name = names_by_key.get(dependency_name.lower())
            if name is not None and name not in reached:
                reached.add(name)
                pending.append(bundled_libraries[name])
    return reached


def main() -> None:
    """Deletes the unreached libraries of the unpacked wheel that the first argument names."""
    wheel_directory = pathlib.Path(sys.argv[1])
    library_directory = wheel_directory / LIBRARY_DIRECTORY_NAME
    bundled_libraries = {
        path.name: path for path in library_directory.iterdir() if path.is_file()
    }
    extension_modules = [
        *wheel_directory.glob("cyipopt/*.so"),
        *wheel_directory.glob("cyipopt/*.pyd"),
    ]
    if not extension_modules:
        raise SystemExit(f"No extension module found in `{wheel_directory}`.")
    loaded_by_path = {
        name for name in bundled_libraries if name.startswith(LOADED_BY_PATH_PREFIXES)
    }
    root_paths = [*extension_modules, *(bundled_libraries[name] for name in loaded_by_path)]
    kept = loaded_by_path | reachable_libraries(root_paths, bundled_libraries)

    for name, path in sorted(bundled_libraries.items()):
        if name not in kept:
            print(f"Removing {name}.")
            path.unlink()
        elif sys.platform == "darwin":
            # Stripping changes the file, which makes the signature that arm64 requires invalid.
            subprocess.run(["strip", "-x", str(path)], check=True)
            subprocess.run(["codesign", "--force", "--sign", "-", str(path)], check=True)


if __name__ == "__main__":
    main()
