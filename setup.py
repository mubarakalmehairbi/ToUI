import setuptools
import sys
from toui import __version__

with open("README.md", "r") as file:
    long_description = file.read()

small = False
if "--small" in sys.argv:
    small = True
    sys.argv.remove('--small')

name = "ToUI"
version = __version__
author = "Mubarak Almehairbi"
description = "Creates user interfaces (websites and desktop apps) from HTML easily"
package_name = "toui"
requirements = []
optional_requirements = ['flask-login', 'flask-sqlalchemy', 'flask-basicauth']

reqs_txt = open("requirements.txt", "r").read()
reqs_txt += "\n" + open("optional_requirements.txt", "r").read()

for pkg in reqs_txt.splitlines():
    pkg_name = pkg.split("==")[0]
    if pkg_name.lower().replace("_","-") in optional_requirements and small:
        continue
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
    package_data={'images': ['images/*']},
    entry_points={'console_scripts': ['toui=toui._cmd:main']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=[package_name],
    install_requires=requirements
)