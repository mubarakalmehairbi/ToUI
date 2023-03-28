import setuptools
from toui import __version__

with open("README.md", "r") as file:
    long_description = file.read()

name = "ToUI"
version = __version__
author = "Mubarak Almehairbi"
description = "Creates user interfaces (websites and desktop apps) from HTML easily"
package_name = "toui"
requirements = []
with open(f"requirements.txt", "rt") as file:
    for pkg in file.read().splitlines():
        pkg_name = pkg.split("==")[0]
        pkg_version = pkg.split("==")[1]
        pkg_major_version = pkg_version.split(".")[0]
        req = f"{pkg_name}>={pkg_version},<{int(pkg_major_version)+1}"
        requirements.append(req)


setuptools.setup(
    name=package_name,
    version=version,
    author=author,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=[package_name],
    install_requires=requirements
)