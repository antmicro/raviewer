# -*- coding: utf-8 -*-
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Updated documentation of the configuration options is available at
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import datetime

from antmicro_sphinx_utils import assets
from antmicro_sphinx_utils.defaults import (
    extensions as default_extensions,
    myst_enable_extensions as default_myst_enable_extensions,
    default_antmicro_html_theme_options,
    default_antmicro_latex_elements
)

# -- General configuration -----------------------------------------------------

# General information about the project.
project = u'Raviewer - User Guide'
basic_filename = 'raviewer--user-guide'
authors = u'Antmicro'
copyright = authors + u', {}'.format(datetime.now().year)

# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''

# This is temporary before the clash between myst-parser and immaterial is fixed
sphinx_immaterial_override_builtin_admonitions = False

numfig = True

# If you need to add extensions just add to those lists
extensions = default_extensions
myst_enable_extensions = default_myst_enable_extensions

myst_substitutions = {
    "project": project
}

today_fmt = '%Y-%m-%d'

pygments_style = 'sphinx'

needs_sphinx = '1.8'

todo_include_todos=False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output ---------------------------------------------------

html_theme = 'sphinx_immaterial'

html_last_updated_fmt = today_fmt

html_show_sphinx = False

html_theme_options = default_antmicro_html_theme_options(pdf_url=f"{basic_filename}.pdf")

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = project

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = str(assets.logo('html'))

# Output file base name for HTML help builder.
htmlhelp_basename = basic_filename

try: html_context
except: html_context = {}
html_context['basic_filename'] = basic_filename

# -- Options for LaTeX output --------------------------------------------------

(
    latex_elements,
    latex_documents,
    latex_logo,
    latex_additional_files
) = default_antmicro_latex_elements(basic_filename, authors, project)

# -- Options for man output --------------------------------------------------

man_pages = [
    ('index', basic_filename, project,
     [authors], 1)
]
