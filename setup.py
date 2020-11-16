import os
from setuptools import setup


def readme():
    with open("README.rst") as f:
        return f.read()


with open(os.path.dirname(__file__) + "/VERSION") as f:
    pkgversion = f.read().strip()


setup(
    name = "runkubejobs",
    version = pkgversion,
    description = "Custom Kubernetes Job Controller for XHPL",
    url = "https://github.com/JustAddRobots/runkubejobs"
    author = "Roderick Constance", 
    author_email = "justaddrobots@icloud",
    license = "Private",
    packages = [
        "runkubejobs",
    ],
    package_data = {
        "runkubejobs": [ 
            "runkubejobs/kube-job-tmpl-runxhpl.yaml", 
        ],
    },
    include_package_data = True,
    install_requires = [
        "kubernetes",
        "python-dateutil",
        "engcommon @ git+ssh://git@engcommon.github.com/JustAddRobots/engcommon.git", ],
    entry_points = {
        "console_scripts": [
            "runkubejobs = runkubejobs.cli:main"
        ],
    },
    zip_safe = False
)
