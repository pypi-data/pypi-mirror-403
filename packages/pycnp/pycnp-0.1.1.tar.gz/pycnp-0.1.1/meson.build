project(
    'pycnp',
    'cpp',
    version: run_command(
        'awk',
        # Matches first line with 'version = "XXX"', and extracts "XXX".
        '/version/ { print $3; exit }',
        'pyproject.toml',
        check: true,
    ).stdout().replace('"', ''),  # turns "XXX" into just XXX
    default_options: [
        'cpp_std=c++20',
        'optimization=3',
        'b_ndebug=if-release',  # disables asserts in release builds
        'b_lto=true',  # enables -flto
        'werror=true',  # promotes warnings to errors
        'warning_level=3',  # sets -Wextra and -Wpedantic
    ]
)

compiler = meson.get_compiler('cpp')
# if compiler.has_argument('-Wno-dangling-reference')
#     # This is a new diagnostic in GCC 13 and up, but it is a bit buggy right
#     # now and issues false positives for some of our code.
#     add_project_arguments('-Wno-dangling-reference', language: 'cpp')
# endif

# Ensure all pybind11 modules share the same internals (for cross-module types)
# Use PYBIND11_INTERNALS_KIND instead of PYBIND11_INTERNALS_ID to avoid macro redefinition
add_project_arguments('-DPYBIND11_INTERNALS_KIND="pycnp_shared"', language: 'cpp')

# We first compile static libraries that contain all regular C++ code. These
# are linked against when we compile the actual Python extension module below.
# We also define the top-level source directory here, for convenience.
SRC_DIR = 'pycnp' / 'cpp'
INCLUDES = include_directories(SRC_DIR)

# 先定义基础库 libgraph（不依赖其他库）
libgraph = static_library(
    'graph',
    [
        SRC_DIR / 'Graph' / 'Graph.cpp',
        SRC_DIR / 'Graph' / 'CNP_Graph.cpp',
        SRC_DIR / 'Graph' / 'DCNP_Graph.cpp',
    ],
    include_directories: INCLUDES,
)

# 然后定义 libsearch（依赖 libgraph）
libsearch = static_library(
    'search',
    [
        SRC_DIR / 'search' / 'BCLSStrategy.cpp',
        SRC_DIR / 'search' / 'CBNSStrategy.cpp',
        SRC_DIR / 'search' / 'CHNSStrategy.cpp',
        SRC_DIR / 'search' / 'DLASStrategy.cpp',
        SRC_DIR / 'search' / 'Search.cpp',
    ],
    include_directories: INCLUDES,
    link_with: libgraph,
)

# 最后定义 libpycnp（依赖 libgraph 和 libsearch）
libpycnp = static_library(
    'core',
    [
        SRC_DIR / 'Population.cpp',
        SRC_DIR / 'ProblemData.cpp',
    ],
    include_directories: INCLUDES, # 包含头文件
    link_with: [libgraph, libsearch],
)

libcrossover = static_library(
    'crossoverlib',
    [
        SRC_DIR / 'crossover' / 'doubleBackboneBasedCrossover.cpp',
        SRC_DIR / 'crossover' / 'inherit_repair_recombination.cpp',
        SRC_DIR / 'crossover' / 'reduceSolveCombine.cpp',
    ],
    include_directories: INCLUDES,
    link_with: [libgraph, libsearch],
)

# Extension modules are specified as [extension name, subdirectory, linked
# static libraries]. The name is the eventual module name, subdirectory gives
# the relative source/installation directory, and the static libraries are the
# ones we defined above.
extensions = [
    ['pycnp', '', [libpycnp, libgraph, libsearch]],
    ['crossover', 'crossover', [libcrossover, libgraph, libsearch]],
]

# Extension dependencies: Python itself, and pybind11.
py = import('python').find_installation()
dependencies = [py.dependency(), dependency('pybind11')]

foreach extension : extensions
    rawname = extension[0]
    name = '_' + rawname
    subdir = extension[1]

    message('Going to build extension module ' + subdir / name + '.')

    # 动态搜索头文件（包含所有子目录）
    doc_search_dir = SRC_DIR / subdir
    doc_glob = 'import glob; print(*glob.glob("' + doc_search_dir + '/**/*.h", recursive=True))'
    doc_cmd = run_command('python', '-c', doc_glob, check: true)
    doc_input_headers = files(doc_cmd.stdout().strip().split())
    pybind_src = SRC_DIR / subdir / 'pybind.cpp'
    if subdir == ''
        pybind_src = SRC_DIR / 'pybind.cpp'
    endif

    doc_output_header = custom_target(
        'docs for ' + name,
        output: rawname + '_docs.h',
        input: ['buildtools/extract_docstrings.py'] + doc_input_headers,
        command: ['python', '@INPUT@', '@OUTPUT@'],
        depend_files: [pybind_src],
        install: false,
        install_dir: 'pycnp' / subdir,
    )

    # Register the extension module to build.
    py.extension_module(
        name,
        [pybind_src, doc_output_header],
        dependencies: dependencies,
        link_with: extension[2],
        install: true,
        subdir: 'pycnp' / subdir,
        include_directories: INCLUDES,
    )
endforeach
