# Sphinx configuration for GuardianLayer documentation.
#
# This file was generated to provide a minimal, useful starting point for
# building documentation with Sphinx. It enables autodoc, napoleon (for
# Google/NumPy-style docstrings), viewcode, and the ReadTheDocs theme.
#
# NOTE: A minimal `index.rst` is required in the same `docs/` directory.
# Example `index.rst` content:
#
# .. Begin example index.rst (save as docs/index.rst) ...
#
# Welcome to GuardianLayer's documentation!
# ========================================
#
# .. toctree::
#    :maxdepth: 2
#    :caption: Contents:
#
#    api
#
# Indices and tables
# ==================
#
# * :ref:`genindex`
# * :ref:`modindex`
# * :ref:`search`
#
# .. End example index.rst
#
# You can also create docs/api.rst with the result of `sphinx-apidoc` or hand
# write the RST that uses automodule/autoclass directives for the package.

import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------

# Ensure the project's `src/` directory is importable so autodoc can import the package.
# Adjust the relative path if your sources are located elsewhere.
HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, "..", "src")  # compatible with repository layout
sys.path.insert(0, os.path.normpath(SRC_DIR))

# -- Project information -----------------------------------------------------

project = "GuardianLayer"
author = "Michael"
copyright = f"{datetime.utcnow().year}, {author}"

# Try to determine the installed package version; if not available, fall back.
try:
    # Python 3.8+: importlib.metadata
    try:
        from importlib.metadata import PackageNotFoundError, version  # type: ignore
    except Exception:
        # For older Pythons or environments, fallback to pkg_resources (setuptools)
        from pkg_resources import DistributionNotFound, get_distribution  # type: ignore

        def _get_version(name):
            try:
                return get_distribution(name).version
            except DistributionNotFound:
                return "0.0.0"

        release = _get_version(project)
    else:
        try:
            release = version(project)
        except PackageNotFoundError:
            # Fallback: read __version__ from package if present
            try:
                import GuardianLayer as _pkg  # type: ignore

                release = getattr(_pkg, "__version__", "0.0.0")
            except Exception:
                release = "0.0.0"
except Exception:
    release = "0.0.0"

# Short X.Y version
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",  # Core: include documentation from docstrings
    "sphinx.ext.napoleon",  # Support for Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.autosummary",  # Generate summary tables and stub pages
    "sphinx.ext.intersphinx",  # Link to other projects' docs (optional)
]

# Optionally mock heavy or optional imports so docs can be built without all deps.
# Add package names here that are imported by the package but not required to build docs.
autodoc_mock_imports = ["aiosqlite"]

# autodoc settings
autodoc_member_order = "bysource"
autoclass_content = "both"  # include both class docstring and __init__ docstring
autodoc_typehints = "description"

# Napoleon settings (works for Google/NumPy-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_ivar = True
napoleon_use_rtype = True

# Autosummary: automatically generate summary pages for modules
autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = None
html_favicon = None
html_title = f"{project} documentation"

# -- Intersphinx mapping -----------------------------------------------------
# Useful to link to Python stdlib and popular libraries. Adjust as needed.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
}

# -- Additional helpful config ------------------------------------------------

# Show the docstring for __init__ on modules if available
add_module_names = False

# Pygments (syntax highlighting) style
pygments_style = "sphinx"

# -- Custom setup ------------------------------------------------------------


def setup(app):
    # Example: add custom CSS if you add files under docs/_static/
    # app.add_css_file("custom.css")
    app.add_config_value("recommonmark_config", {}, True)
    return
