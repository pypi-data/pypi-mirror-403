import datetime
import importlib
import inspect
import json
import os
import subprocess
import sys

import tomllib

# -- Project information
sys.path.insert(0, os.path.abspath("../../"))

now = datetime.date.today()

project = "PyCNP"
authors = "Bo Xue"
repo_url = "https://github.com/xuebo100/PyCNP/"
copyright = f"2025 - {now.year}, {authors}"

with open("../../pyproject.toml", "rb") as fh:
    pyproj = tomllib.load(fh)
    release = version = pyproj["project"]["version"]

versions_file = os.path.join(os.path.dirname(__file__), "versions.json")
with open(versions_file) as fh:
    version_info = json.load(fh)

# -- API documentation
autoclass_content = "class"
autodoc_member_order = "bysource"
autodoc_typehints = "signature"
autodoc_preserve_defaults = True


# -- sphinx.ext.linkcode
def linkcode_resolve(domain: str, info: dict) -> str | None:
    """
    Generates a URL pointing to the source code of a specified object located
    in the PyCNP repository.
    """
    if domain != "py" or not info.get("module") or not info.get("fullname"):
        return None

    obj = importlib.import_module(info["module"])
    for attr_name in info["fullname"].split("."):
        try:
            obj = getattr(obj, attr_name)
        except AttributeError:
            return None

    try:
        source = inspect.getsourcefile(obj)
    except TypeError:
        return None

    if source is None:
        return None

    # Determine relative path
    # If installed in editable mode, source might be absolute path to local file
    # We want path relative to project root
    
    # Try to find pycnp/ in the path
    idx = source.find("pycnp/")
    if idx != -1:
        rel_path = source[idx:]
    else:
        # Fallback for unexpected paths
        return None

    try:
        line_num = inspect.getsourcelines(obj)[1]
    except OSError:
        # Could happen if source file is modified after import or other issues
        line_num = 1

    # Get current commit hash
    try:
        cmd = ["git", "rev-parse", "--short", "HEAD"]
        revision = subprocess.check_output(cmd).strip().decode("ascii")
    except subprocess.CalledProcessError:
        revision = "main" # Fallback

    return f"{repo_url}blob/{revision}/{rel_path}#L{line_num}"


# -- numpydoc
numpydoc_xref_param_type = True
numpydoc_class_members_toctree = False
numpydoc_attributes_as_param_list = False
napoleon_include_special_with_doc = True

# -- General configuration
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "myst_parser",
]

exclude_patterns = ["_build", "**.ipynb_checkpoints"]

# Suppress specific warnings
suppress_warnings = ["misc.highlighting_failure"]

# Numpydoc configuration - enable basic validation checks
# See https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-checks
numpydoc_validation_checks = [
    "SS01",  # Summary must fit on one line
    "SS02",  # Summary does not start with capital letter
    "SS03",  # Summary does not end with period
    "GL01",  # Deprecated tag is present
    "GL02",  # Deprecated tag is empty
    "GL03",  # Yields tag is empty
    "PR01",  # Parameters section not found
    "SA01",  # See Also section not alphabetized
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

add_module_names = False
python_use_unqualified_type_names = True

# -- Options for HTML output
# html_theme = "sphinx_immaterial"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
# html_logo = "assets/images/icon.svg" # No logo yet
html_theme_options = {
    "logo_only": False,
    # "display_version": True,  # Not supported by sphinx_rtd_theme
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    # "style_nav_header_background": "white",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False
}

python_resolve_unqualified_typing = True
python_transform_type_annotations_pep585 = True
python_transform_type_annotations_pep604 = True
object_description_options = [
    ("py:.*", dict(include_fields_in_toc=False, include_rubrics_in_toc=False)),
    ("py:attribute", dict(include_in_toc=False)),
    ("py:parameter", dict(include_in_toc=False)),
]
