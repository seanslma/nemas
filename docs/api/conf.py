# -- Path setup --------------------------------------------------------------
import os
import sys
from datetime import datetime

# Add the project root to the path so Sphinx can find the 'nemas' package
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
project = 'nemas'
copyright = '2026, Sean Ma'
author = 'Sean Ma'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
extensions = [
    # Core Sphinx extensions
    'sphinx.ext.autodoc',  # To include documentation from docstrings
    'sphinx.ext.viewcode',  # To link to the source code
    'sphinx.ext.autosummary',  # To automatically generate summary tables
    # Additional utility extensions
    # 'sphinx_autodoc_typehints',  # To display type hints nicely
    'numpydoc',  # To support NumPy style docstrings
    'sphinx_design',  # For badges, cards, etc.
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',  # To add copy buttons to code blocks
]

# Strip the >>> and ... prompts so copied code is clean
copybutton_prompt_text = '>>> |\\.\\.\\. '
copybutton_prompt_is_regexp = True

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# The theme to use. This enables the PyData Sphinx Theme.
html_theme = 'pydata_sphinx_theme'

# The theme options
html_theme_options = {
    'github_url': 'https://github.com/seanslma/nemas',
    'secondary_sidebar_items': [],  # Disable the secondary sidebar items (page toc)
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom CSS files
html_css_files = [
    'custom.css',
]

# If true, the rest sources are included in the HTML build as _sources/foo.txt.
html_copy_source = False

# disable default copyright
html_show_copyright = False

# Add back to home link and copyright in the footer
html_context = {
    'copyright_html': f'<a href="/" title="Go to Main Home Page">🏠 Back to Home</a><br>Copyright &copy; {datetime.now().year} Sean Ma'
}

# If true, "Created using Sphinx" is shown in the HTML footer.
html_show_sphinx = True

# -- Autodoc configuration ---------------------------------------------------
# Type hints: show in signature only (not in description)
# autodoc_typehints = "signature"

# Use short format for type hints
# autodoc_typehints_format = "short"

# Preserve the defaults in signatures
autodoc_preserve_defaults = True

# -- Sphinx autodoc typehints configuration ----------------------------------
# This prevents duplicate parameter documentation in the body
# typehints_defaults = "comma"

# -- Numpydoc configuration ---------------------------------------------------
# Don't show class members automatically
numpydoc_show_class_members = False

# Don't show type hints in the parameter descriptions since they're in signature
numpydoc_show_type_hint = False

# Mock imports for modules that are not available in the documentation environment
autodoc_mock_imports = []

# Global setup for doctests
doctest_global_setup = """
import numpy as np
import polars as pl
# anything else needed globally
"""
