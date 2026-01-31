# Configuration file for the Sphinx documentation builder.  # noqa: D100
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("./_extensions"))
# import recommonmark
# from recommonmark.transform import AutoStructify
from calibpipe import __version__

# -- Project information -----------------------------------------------------

project = "calibpipe"
copyright = "2022, UniGE-CTA DPPS CalibPipe Group"
author = "UniGE-CTA DPPS CalibPipe Group"

# The short X.Y version.
version = __version__
# The full version, including alpha/beta/rc tags.
release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx_paramlinks",
    "myst_parser",
    "sphinxarg.ext",
    "nbsphinx",
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx_changelog",
    "cwl_workflow",  # local extension
]

myst_enable_extensions = [
    "linkify",
]

myst_heading_anchors = 3

# Default options for autodoc directives
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,
    "inherited-members": False,
    "exclude-members": "__weakref__, type",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "ctapipe": ("https://ctapipe.readthedocs.io/en/stable/", None),
}


nitpick_ignore_regex = [
    (r"py:.*", r"sqlalchemy.*"),
    (r"py:.*", r"_types.*"),
    (r"py:attr", r"engine"),
    (r"py:meth", r"__exit__"),
    (r"py:attr", r"session"),
    (r"py:class", r"psycopg\.abc\.AdaptContext"),
    (r"py:class", r"calibpipe\.database\.connections\.postgres_utils\._NPIntDumper"),
    (r"py:class", r"types\.TypeEngine"),
    (r"py:class", r"_sqltypes\.Float"),
    (r"py:class", r"Dialect"),
    (r"py:class", r"_BindProcessorType"),
    (r"py:class", r"_ResultProcessorType"),
    (r"py:paramref", r"_sqltypes\.Float\._sphinx_paramlinks_precision"),
    (r"py:class", r"_oracle\.FLOAT"),
    (r"py:paramref", r"_oracle\.FLOAT\._sphinx_paramlinks_binary_precision"),
    (r"py:class", r"mysql\.TIME"),
    (r"py:class", r"ExternalType"),
    (r"py:class", r"TypeDecorator"),
    (r"py:class", r"UserDefinedType"),
    (r"py:class", r"Unicode"),
    (r"py:class", r"UnicodeText"),
    (r"py:class", r"_schema\.Column"),
    (r"py:class", r"enum\.Enum"),
    (r"undefined label", r"constraint_naming_conventions"),
    (r"undefined label", r"types_typedecorator"),
    (r"undefined label", r"sql_caching"),
    (r"term not in glossary", r"DBAPI"),
    (r"misc.highlighting_failure", r"Pygments lexer name 'pycon\+sql' is not known"),
]

suppress_warnings = ["misc.highlighting_failure"]

# autosectionlabel_prefix_document = True

# Generate todo blocks
todo_include_todos = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document.
master_doc = "index"

# Ignore example notebook errors
nbsphinx_allow_errors = True
nbsphinx__timeout = 200  # allow max 2 minutes to build each notebook

numpydoc_show_class_members = False

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["changes"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "ctao"
html_theme_options = dict(
    navigation_with_keys=False,
    logo=dict(text="CalibPipe"),
    # setup for displaying multiple versions, also see setup in .gitlab-ci.yml
    switcher=dict(
        json_url="http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/versions.json",  # noqa: E501
        version_match="latest" if ".dev" in version else f"v{version}",
    ),
    navbar_center=["version-switcher", "navbar-nav"],
)

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
