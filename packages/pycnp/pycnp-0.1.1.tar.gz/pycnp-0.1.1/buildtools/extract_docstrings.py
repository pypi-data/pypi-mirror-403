"""
This script extracts the docstrings from various C++ header files, and writes
them into a documentation header file. This is used to generate documentation
on the fly as Meson compiles the extensions.
"""

import argparse
import pathlib

import docblock

# The macros below are shamelessly taken from pybind11_mkdocs, here:
# https://github.com/pybind/pybind11_mkdoc.
_PREFIX = """
// Auto-generated during compilation. Do not edit.

#define __EXPAND(x) x
#define __COUNT(_1, _2, _3, _4, _5, _6, _7, COUNT, ...) COUNT
#define __VA_SIZE(...) __EXPAND(__COUNT(__VA_ARGS__, 7, 6, 5, 4, 3, 2, 1, 0))
#define __CAT1(a, b) a ## b
#define __CAT2(a, b) __CAT1(a, b)
#define __DOC1(n1) PYCNP_doc_##n1
#define __DOC2(n1, n2) PYCNP_doc_##n1##_##n2
#define __DOC3(n1, n2, n3) PYCNP_doc_##n1##_##n2##_##n3
#define __DOC4(n1, n2, n3, n4) PYCNP_doc_##n1##_##n2##_##n3##_##n4
#define __DOC5(n1, n2, n3, n4, n5) PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5
#define __DOC6(n1, n2, n3, n4, n5, n6) \
    PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5##_##n6
#define __DOC7(n1, n2, n3, n4, n5, n6, n7) \
    PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5##_##n6##_##n7
#define DOC(...) \
    __EXPAND(__EXPAND(__CAT2(__DOC, __VA_SIZE(__VA_ARGS__)))(__VA_ARGS__))
#define DOC_IMPL(...) DOC(__VA_ARGS__)

#if defined(__GNUG__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
#endif
"""

_SUFFIX = """
#if defined(__GNUG__)
#pragma GCC diagnostic pop
#endif
"""


# A non-exhaustive mapping from C++ operators to Python's equivalents. This
# is used to give the documentation strings proper variable names. Extend this
# list if your build complains.
_OP2DUNDER = {
    "operator[]": "__getitem__",
    "operator()": "__call__",
}

# Fallback symbols for which docblock cannot find documentation.
# These should only include symbols that truly lack C++ header comments.
# Most symbols now have proper Doxygen comments in their header files.
FALLBACK_SYMBOLS = {
    # Population::initialize (still inline - docblock cannot parse)
    "Population::initialize": (
        "initialize\n\nInitializes the population with diverse solutions.\n\n"
        "Generates initial solutions using local search with random "
        "starting points.\n\n"
        "Returns\n-------\nTuple[Solution, int]\n"
        "Pair of (best initial solution, its objective value)"
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(prog="extract_docstrings")

    parser.add_argument(
        "input_locs",
        nargs="+",
        type=pathlib.Path,
        help="Files from which to extract docstrings.",
    )
    parser.add_argument(
        "output_loc",
        type=pathlib.Path,
        help="Where to write the docstrings.",
    )

    return parser.parse_args()


def to_cpp_stmt(name: str, docstrings: list[str]) -> str:
    # Turns the fully qualified name into something separated by underscores.
    # C++ operator overloads are mapped to their Python equivalents because
    # a C++ operator overload is not a valid variable name.
    parts = name.split("::")
    parts[-1] = _OP2DUNDER.get(parts[-1], parts[-1])
    var_name = "PYCNP_doc_" + "_".join(parts)

    # Structure of the C++ statement we are going to write.
    cpp_stmt = 'static char const *{var_name} = R"doc(\n{doc}\n)doc";'

    unique_docs: list[str] = []
    for doc in docstrings:
        if doc not in unique_docs:
            unique_docs.append(doc)

    docstrings = unique_docs

    if len(docstrings) == 0:
        docstrings = ["Documentation missing."]

    stmts = [cpp_stmt.format(var_name=var_name, doc=docstrings[0])]

    for ctr, doc in enumerate(docstrings[1:], 2):
        stmts.append(cpp_stmt.format(var_name=f"{var_name}_{ctr}", doc=doc))

    return "\n".join(stmts)


def main():
    args = parse_args()

    parsed = {}
    for header in args.input_locs:
        parsed.update(docblock.parse_file(header))

    for symbol, docstring in FALLBACK_SYMBOLS.items():
        parsed.setdefault(symbol, [docstring])

    # Filter out internal helper names docblock finds that do not map to any
    # bound Python symbol.
    parsed.pop("Population::isDuplicate::size", None)

    docs = "\n".join(map(lambda item: to_cpp_stmt(*item), parsed.items()))

    with open(args.output_loc, "w") as fh:
        for section in [_PREFIX, docs, _SUFFIX]:
            fh.write(section)
            fh.write("\n")


if __name__ == "__main__":
    main()
