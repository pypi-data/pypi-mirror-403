import sysconfig

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


# Entry point for main Orange categories/widgets discovery
def widget_discovery(discovery):
    from ewoksorange.pkg_meta import get_distribution

    dist = get_distribution("ewoksxrdct")
    pkgs = [
        "orangecontrib.ewoksxrdct.categories.examples1",
        "orangecontrib.ewoksxrdct.categories.examples2",
    ]
    for pkg in pkgs:
        discovery.process_category_package(pkg, distribution=dist)
