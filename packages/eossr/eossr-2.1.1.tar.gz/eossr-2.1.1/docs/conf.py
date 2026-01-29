# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import glob
import os
import shutil
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

# Notebooks
notebook_dir = '../examples/notebooks/'
os.makedirs('examples', exist_ok=True)
[shutil.copy(notebook_dir + file, 'examples')
 for file in os.listdir(notebook_dir) if file.endswith('.ipynb')]

# Snippets
snippets_doc_dir = 'snippets'
os.makedirs(snippets_doc_dir, exist_ok=True)
for filename in glob.glob('../examples/CI_code_snippets/*.md'):
    shutil.copy(filename, snippets_doc_dir)


# -- Project information -----------------------------------------------------

project = 'eossr'
copyright = '2021, ESCAPE OSSR developers and contributors'
author = 'Thomas Vuillaume & Enrique Garcia'

release = ''

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'nbsphinx',
    'sphinx.ext.viewcode',
    'myst_parser',
    'sphinx_multiversion',
    'sphinxcontrib.autoprogram',
    'sphinxcontrib.mermaid',
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

html_sidebars = {
    '**': [
        'versioning.html',
    ],
}

# Parsers
# source_parsers = {
# }

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = [
    '.rst',
    '.md',
]


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# nbsphinx
nbsphinx_allow_errors = False
nbsphinx_execute = 'auto'  # default:'auto', disable with 'never', force with 'always'

# sphinx-multiversion
# Whitelist pattern for tags (set to None to ignore all tags)
smv_tag_whitelist = r'^.*$'

# Whitelist pattern for branches (set to None to ignore all branches)
# smv_branch_whitelist = r'^.*$'
smv_branch_whitelist = 'master'

# Whitelist pattern for remotes (set to None to use local branches only)
smv_remote_whitelist = None

# Pattern for released versions
smv_released_pattern = r'.*v.*'

# Format for versioned output directories inside the build directory
smv_outputdir_format = '{ref.name}'

# Determines whether remote or local git branches/tags are preferred if their output dirs conflict
smv_prefer_remote_refs = False
