# Configuration file for the Sphinx documentation builder.
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
# import sphinx_bootstrap_theme
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'stdopen'
copyright = '2023, Chris Finan'
author = 'Chris Finan'

# The full version, including alpha/beta/rc tags
release = '0.2.2'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "sphinx_rtd_theme",
    "myst_parser",
    "nbsphinx",
    "nbsphinx_link",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    # 'sphinx.ext.viewcode',
    "sphinx.ext.intersphinx"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'sphinx_rtd_theme'
# Activate the theme.
# html_theme = 'furo'
html_theme = 'sphinx_book_theme'

# Theme options are theme-specific and customize the look and feel of a
# theme further.
# html_theme_options = {
#     # Bootswatch (http://bootswatch.com/) theme.
#     #
#     # Options are nothing (default) or the name of a valid theme
#     # such as "cosmo" or "sandstone".
#     #
#     # The set of valid themes depend on the version of Bootstrap
#     # that's used (the next config option).
#     #
#     # Currently, the supported themes are:
#     # - Bootstrap 2: https://bootswatch.com/2
#     # - Bootstrap 3: https://bootswatch.com/3
#     'bootswatch_theme': "spacelab",
# }

# html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Intersphinx, links into the STD python library
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
