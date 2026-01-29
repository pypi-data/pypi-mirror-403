# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import re

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath("../../"))


def convert_markdown_code_blocks(app, what, name, obj, options, lines):
    """Convert markdown-style code blocks (```python) to reStructuredText format."""
    if not lines:
        return
    
    new_lines = []
    in_code_block = False
    code_language = None
    code_content = []
    
    for line in lines:
        # Check for markdown code block start (```language or ```)
        match_start = re.match(r'^\s*```(\w+)?\s*$', line)
        if match_start and not in_code_block:
            # Start of code block
            in_code_block = True
            code_language = match_start.group(1) or 'python'
            continue
        
        # Check for markdown code block end (```)
        if in_code_block and re.match(r'^\s*```\s*$', line):
            # End of code block - convert to reStructuredText
            new_lines.append('')
            new_lines.append(f'.. code-block:: {code_language or "python"}')
            new_lines.append('')
            for code_line in code_content:
                new_lines.append('   ' + code_line)
            new_lines.append('')
            code_content = []
            in_code_block = False
            code_language = None
            continue
        
        if in_code_block:
            code_content.append(line)
        else:
            new_lines.append(line)
    
    # Handle unclosed code block (shouldn't happen, but be safe)
    if in_code_block:
        new_lines.append('')
        new_lines.append(f'.. code-block:: {code_language or "python"}')
        new_lines.append('')
        for code_line in code_content:
            new_lines.append('   ' + code_line)
        new_lines.append('')
    
    lines[:] = new_lines

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pydantic-ai-toolsets'
copyright = '2026, Shreyans Maini'
author = 'Shreyans Maini'
# Get version from package
try:
    from pydantic_ai_toolsets import __version__
    release = __version__
    version = '.'.join(__version__.split('.')[:2])  # Major.minor for version
except ImportError:
    # Fallback if package not installed
    release = '0.2.2'
    version = '0.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "myst_parser",
]

templates_path = ['_templates']
exclude_patterns = []

# Source file suffixes
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True  # Enable for better code block rendering
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True
napoleon_convert_quotes = True  # Convert quotes for better compatibility

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': False,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

# Suppress some warnings
suppress_warnings = [
    'autosectionlabel.*',  # Suppress autosectionlabel warnings
]

autodoc_mock_imports = []

# Intersphinx mapping for external documentation
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
    'pydantic-ai': ('https://ai.pydantic.dev/', None),
}

# Autosummary settings
autosummary_generate = True

# MyST Parser settings
# Note: linkify requires linkify-it-py package, removed to avoid dependency issues
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3
myst_substitutions = {}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "conestack"

# Only include _static if it exists
static_path = os.path.join(os.path.dirname(__file__), '_static')
html_static_path = ['_static'] if os.path.exists(static_path) else []

# Conestack theme options
# See https://conestack.github.io/sphinx-conestack-theme for full options
html_theme_options = {
    # Add theme-specific options here if needed
    # The theme will use sensible defaults
}

# Pygments style for code highlighting
pygments_style = 'default'
pygments_dark_style = 'monokai'

# Code block options
highlight_language = 'python3'

# Setup function to register custom processors
def setup(app):
    """Setup function for Sphinx."""
    # Connect the markdown code block converter to autodoc
    app.connect('autodoc-process-docstring', convert_markdown_code_blocks)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
