"""Lists the DLLs that each binary of an extracted Windows wheel imports.

The first argument is the directory that holds the extracted wheel. The script
reads the import tables of every DLL and extension module below that directory.
"""

import pathlib
import sys

import pefile


def main() -> None:
    """Prints each binary under the directory with the DLL names it imports."""
    extracted_directory = pathlib.Path(sys.argv[1])
    binary_paths = sorted(
        [*extracted_directory.rglob("*.dll"), *extracted_directory.rglob("*.pyd")]
    )
    for binary_path in binary_paths:
        portable_executable = pefile.PE(str(binary_path), fast_load=True)
        portable_executable.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        imported_names = sorted(
            {entry.dll.decode() for entry in portable_executable.DIRECTORY_ENTRY_IMPORT}
        )
        relative_path = binary_path.relative_to(extracted_directory)
        print(f"{relative_path}: {', '.join(imported_names)}")


if __name__ == "__main__":
    main()
