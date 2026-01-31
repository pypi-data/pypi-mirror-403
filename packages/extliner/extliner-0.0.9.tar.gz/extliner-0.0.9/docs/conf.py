from datetime import datetime

project = 'extliner'
release = '0.0.9'
year = datetime.now().year
copyright = f"{year} CodePerfectPlus"

# Paths and source setup
templates_path = ['_templates']
source_suffix = ".rst"
master_doc = "index"
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']
html_static_path = ['_static']

# Extensions for Sphinx
extensions = [
    'sphinx.ext.autodoc',    # Generate docs from docstrings
    'sphinx.ext.todo',       # Support TODO directives
    'sphinx.ext.coverage',   # Documentation coverage
    'sphinx.ext.viewcode',   # Link to source code in docs
    'sphinx.ext.autosectionlabel',  # Reference sections automatically
    'sphinx.ext.githubpages',  # GitHub Pages support
]

# Avoid ambiguous section labels
autosectionlabel_prefix_document = True

# PDF generation (optional)
pdf_documents = [
    ('index', 'Extliner_Documentation', 'Extliner Docs', 'Extliner Team')
]

# GitHub releases integration
releases_github_path = "codeperfectplus/extliner"
releases_unstable_prehistory = True

# HTML output options
html_theme = 'pydata_sphinx_theme'  # Nice modern theme
# alternatives: 'sphinx_rtd_theme'
html_theme_options = {
    "show_prev_next": True,
    "navigation_depth": 4,
    "collapse_navigation": True,
    "navbar_align": "content",
    "show_nav_level": 2,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/codeperfectplus/extliner",
            "icon": "fab fa-github",
            "type": "fontawesome"
        },
        {
            "name": "Releases",
            "url": "https://github.com/codeperfectplus/extliner/releases",
            "icon": "fas fa-tag",
            "type": "fontawesome"
        }
    ],
    "use_edit_page_button": True,
}

# GitHub edit button context
html_context = {
    "github_user": "codeperfectplus",
    "github_repo": "extliner",
    "github_version": "main",
    "doc_path": "docs",
}

# Sidebars config
html_sidebars = {
    '**': [
        'globaltoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html'
    ]
}

# Additional CSS files (add custom styles if any)
html_css_files = [
    'custom.css',
]
