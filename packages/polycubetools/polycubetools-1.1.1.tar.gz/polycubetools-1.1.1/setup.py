import re

import setuptools


def version():
    with open("src/polycubetools/__init__.py") as f:
        return re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)  # type: ignore


setuptools.setup(version=version())
