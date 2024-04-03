# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

#import os
#import sys
#sys.path.insert(0, os.path.abspath("../../src/"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'range-time-plot'
copyright = '2024, jsatuit'
author = 'jsatuit'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autoapi.extension',
    'sphinx.ext.autodoc.typehints',
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]
autoapi_dirs = ['../../src']
autodoc_typehints = 'description'

myst_enable_extensions = ["colon_fence"]
templates_path = ['_templates']
exclude_patterns = []

def skip_util_classes(app, what, name, obj, skip, options):
    if what == "data" and "start_name_main_block" in name:
        skip = True
    return skip
def setup(sphinx):
   sphinx.connect("autoapi-skip-member", skip_util_classes)

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
