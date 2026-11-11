project(
  'cyipopt',
  'c',
  version: '1.7.0',
  meson_version: '>=1.8',
  default_options: ['c_std=c11', 'buildtype=release', 'b_ndebug=if-release'],
)

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

subdir('cyipopt')
