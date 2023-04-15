# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os
from toui import __version__
sys.path.insert(0,os.path.abspath('..'))

project = 'ToUI'
copyright = '2023, Mubarak Almehairbi'
author = 'Mubarak Almehairbi'
release = __version__
master_doc = 'index'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.viewcode','sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.todo',
              'sphinx.ext.autosummary', 'myst_parser', 'sphinx.ext.intersphinx']
autodoc_default_flags = ['members']
autoclass_content = 'both'
intersphinx_mapping = {
    "flask": ("https://flask.palletsprojects.com/en/2.2.x/", None),
    "werkzeug": ("https://werkzeug.palletsprojects.com/en/2.2.x/", None),
    "bs4": ("https://www.crummy.com/software/BeautifulSoup/bs4/doc/", None),
    "simple_websocket": ("https://simple-websocket.readthedocs.io/en/latest/", None),
    "flask_sock": ("https://flask-sock.readthedocs.io/en/latest/", None),
}
autosummary_generate = False
html_logo = "images/logo.png"
templates_path = ['_templates']
language = 'en'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_theme_options = {
   "show_nav_level": 2,
   "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/mubarakalmehairbi/ToUI",
            "icon": "fab fa-github-square fa-2x",
            "type": "fontawesome",
        }
   ]
}
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]