"""
Wrapper around the build_extensions script. We compile in a temporary Meson
build directory so the default build backend (and tools like ``uv``) can build
in isolation without polluting the working tree.
"""

import pathlib
import tempfile

from build_extensions import build, clean


def main():
    cwd = pathlib.Path.cwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        build_dir = pathlib.Path(tmpdir)
        install_dir = cwd / "pycnp"

        clean(build_dir, install_dir)
        build(build_dir, build_type="release", verbose=False)


if __name__ == "__main__":
    main()
