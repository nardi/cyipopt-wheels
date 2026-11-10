"""Chooses the cyipopt version to build and checks for an existing release.

The version is the newest release on PyPI unless `REQUESTED_VERSION` names one.
The script writes `version`, `tag` and `build` to the file that `GITHUB_OUTPUT`
names. `build` is `false` when the repository already has a release for the tag.
"""

import json
import os
import re
import subprocess
import urllib.request

PYPI_PROJECT_URL = "https://pypi.org/pypi/cyipopt/json"
VERSION_PATTERN = re.compile(r"[0-9][0-9A-Za-z.]*")


def latest_pypi_version() -> str:
    """Returns the newest stable cyipopt version listed on PyPI."""
    with urllib.request.urlopen(PYPI_PROJECT_URL, timeout=60) as response:
        return json.load(response)["info"]["version"]


def release_exists(repository: str, tag: str) -> bool:
    """Returns whether `repository` has a release named `tag`."""
    result = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repository],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    if "not found" in result.stderr.lower():
        return False
    raise RuntimeError(
        f"Could not query the release `{tag}`: {result.stderr.strip()}"
    )


def main() -> None:
    """Writes the chosen version and the build decision to `GITHUB_OUTPUT`."""
    repository = os.environ["GITHUB_REPOSITORY"]
    requested_version = os.environ.get("REQUESTED_VERSION", "").strip()
    if requested_version and not VERSION_PATTERN.fullmatch(requested_version):
        raise SystemExit(f"Invalid cyipopt version: `{requested_version}`.")

    version = requested_version or latest_pypi_version()
    tag = f"v{version}"
    build = not release_exists(repository, tag)

    if build:
        print(f"No release `{tag}` in {repository}. Building cyipopt {version}.")
    else:
        print(f"Release `{tag}` already exists in {repository}. Nothing to build.")

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output_file:
        output_file.write(f"version={version}\n")
        output_file.write(f"tag={tag}\n")
        output_file.write(f"build={str(build).lower()}\n")


if __name__ == "__main__":
    main()
