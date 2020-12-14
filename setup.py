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
    description = "Custom Kubernetes Job Controller",
    url = "https://github.com/JustAddRobots/runkubejobs",
    author = "Roderick Constance",
    author_email = "justaddrobots@icloud.com",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    python_requires=">=3",
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
        "engcommon @ git+https://github.com/JustAddRobots/engcommon.git",
    ],
    entry_points = {
        "console_scripts": [
            "runkubejobs = runkubejobs.cli:main"
        ],
    },
    zip_safe = False
)
