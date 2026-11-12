project(
  'cyipopt',
  'c',
  version: '1.7.0',
  meson_version: '>=1.8',
  default_options: ['c_std=c11', 'buildtype=release', 'b_ndebug=if-release'],
)

fs = import('fs')
python = import('python').find_installation(pure: false)
cython = find_program('cython')

# The JLL wraps in `subprojects` come from `meson-jll`, which the build writes before Meson
# parses this file.
ipopt = dependency('Ipopt_jll')

# Ipopt calls BLAS and LAPACK through libblastrampoline, which forwards them to a backend only
# after one is loaded. OpenBLAS is linked in so that the extension can forward it on import.
# OpenBLAS32 has 32-bit integers, which the MUMPS and SPRAL libraries use as well.
openblas = dependency('OpenBLAS32_jll')
lbt = dependency('libblastrampoline_jll')

# The NumPy headers are outside the source tree, and `include_directories` refuses absolute
# paths, so the directory goes in as a compiler argument.
numpy_include = run_command(
  python, '-c', 'import numpy; print(numpy.get_include())', check: true,
).stdout().strip()
numpy = declare_dependency(compile_args: ['-I' + numpy_include])

# The header that cyipopt includes as `IpStdCInterface.h` sits in `include/coin-or` of the Ipopt
# tarball, and the wrap does not put that directory on the include path. The wrap is extracted by
# now, because the dependency above has been resolved, so the directory is found and passed on.
ipopt_header = run_command(
  python, '-c', 'import glob, sys; print(glob.glob(sys.argv[1], recursive=True)[0])',
  meson.project_source_root() / 'subprojects' / '**' / 'coin-or' / 'IpStdCInterface.h',
  check: true,
).stdout().strip()
ipopt_headers = declare_dependency(compile_args: ['-I' + fs.parent(ipopt_header)])

subdir('cyipopt')
