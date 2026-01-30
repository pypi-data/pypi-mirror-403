import sysconfig

NAME = "ewoksxrdct"

DESCRIPTION = "An Ewoks project"

LONG_DESCRIPTION = "An Ewoks project"

ICON = "icons/category.svg"

BACKGROUND = "light-blue"

WIDGET_HELP_PATH = (
    # Development documentation (make htmlhelp in ./doc)
    ("{DEVELOP_ROOT}/doc/_build/htmlhelp/index.html", None),
    # Documentation included in wheel
    (
        "{}/help/ewoksxrdct/index.html".format(sysconfig.get_path("data")),
        None,
    ),
    # Online documentation url
    ("https://ewoksxrdct.readthedocs.io", ""),
)
