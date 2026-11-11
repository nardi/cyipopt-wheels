# cyipopt-wheels

Wheels for [cyipopt](https://github.com/mechmotum/cyipopt) with Ipopt and its
numerical libraries bundled into each wheel. Installing a wheel does not
require a system copy of Ipopt.

## Releases

The workflow in `.github/workflows/build-wheels.yml` checks PyPI for the newest
cyipopt release. When this repository has no release named `v<version>`, the
workflow builds the wheels and publishes them as a GitHub release.

Each release holds one wheel per Python version and platform:

- Python 3.11, 3.12, and 3.13
- Linux x86_64, tagged `manylinux_2_28`
- macOS arm64 (Apple silicon)
- Windows AMD64

Install a wheel with pip by passing the URL of the wheel for your Python
version and platform. For example, Python 3.13 on Linux with cyipopt 1.7.0:

```bash
python -m pip install https://github.com/nardi/cyipopt-wheels/releases/download/v1.7.0/cyipopt-1.7.0-cp313-cp313-manylinux_2_28_x86_64.whl
```

## Build steps

Each build downloads the cyipopt sdist from PyPI, writes the Ipopt and OpenBLAS wraps with
`meson-jll`, and builds the wheel with `meson-python`. The binaries come from the Julia binary
builders. On Linux and macOS the repair tool, `auditwheel` or `delocate`, bundles the shared
libraries that the wheel needs from outside the wheel. The Windows wheel keeps the DLLs that
`meson-python` bundles, because `delvewheel` cannot see them. The Linux wheels are built inside
the `manylinux_2_28` image.

## Schedule and manual runs

The workflow runs every day at 05:23 UTC. It also runs on demand from the
Actions tab. A manual run takes two optional inputs:

- `version` builds a specific cyipopt version. Leave it empty to build the
  newest release.
- `publish` creates the release when it is `true`. Set it to `false` to build
  and test without creating a release.

A run stops without building when the repository already has a release for the
chosen version.

## Validation

Each wheel is installed into a new virtual environment on a fresh runner that
has no Ipopt. The `scripts/smoke_test.py` script then solves Hock and
Schittkowski problem 71. The release is created only when every wheel passes.

## Legacy wheel

`cyipopt-1.4.1-cp311-cp311-manylinux_2_28_x86_64.whl` is the wheel this
repository hosted before the workflow existed. It remains in the repository as
it was.
