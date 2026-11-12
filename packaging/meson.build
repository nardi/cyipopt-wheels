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
ipopt_jll = dependency('Ipopt_jll')

# Ipopt calls BLAS and LAPACK through libblastrampoline, which forwards them to a backend only
# after one is loaded. The package forwards the bundled OpenBLAS to it on import.
# OpenBLAS32 has 32-bit integers, which the MUMPS and SPRAL libraries use as well.
# The package loads both libraries by path, so the extension does not link against them. The
# calls are still needed, because they make the wraps install the libraries into the wheel.
dependency('OpenBLAS32_jll')
dependency('libblastrampoline_jll')

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

# The dependency of the wrap links against every library of the Ipopt tarball, which would make
# the loader require all of them. The extension only calls Ipopt itself, so on Linux and macOS it
# links against that one library by path. MSVC records only the DLLs whose symbols are used, so
# Windows keeps the dependency of the wrap, which also provides the import library.
if host_machine.system() == 'windows'
  ipopt = ipopt_jll
else
  ipopt_library_name = host_machine.system() == 'darwin' ? 'libipopt.dylib' : 'libipopt.so'
  ipopt_library = run_command(
    python, '-c', 'import glob, sys; print(glob.glob(sys.argv[1], recursive=True)[0])',
    meson.project_source_root() / 'subprojects' / '**' / 'lib' / ipopt_library_name,
    check: true,
  ).stdout().strip()
  ipopt = declare_dependency(link_args: [ipopt_library])
endif

subdir('cyipopt')
