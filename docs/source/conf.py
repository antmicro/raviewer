# -*- coding: utf-8 -*-
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Updated documentation of the configuration options is available at
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import datetime

from antmicro_sphinx_utils.defaults import (
    extensions as default_extensions,
    myst_enable_extensions as default_myst_enable_extensions,
    default_antmicro_html_theme_options,
    default_antmicro_latex_elements,
    html_logo as default_html_logo,
    antmicro_html_theme_options,
    antmicro_latex_elements

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

todo_include_todos=False

# -- Options for HTML output ---------------------------------------------------

html_theme = 'sphinx_immaterial'

html_last_updated_fmt = today_fmt

html_show_sphinx = False

html_theme_options = antmicro_html_theme_options(pdf_url=f"{basic_filename}.pdf")

html_title = project

html_logo = default_html_logo

# -- Options for LaTeX output --------------------------------------------------

(
    latex_elements,
    latex_documents,
    latex_logo,
    latex_additional_files
) = antmicro_latex_elements(basic_filename, authors, project)

# -- Options for man output --------------------------------------------------

man_pages = [
    ('index', basic_filename, project,
     [authors], 1)
]
