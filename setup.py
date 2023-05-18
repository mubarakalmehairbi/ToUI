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
version = __version__ + "+1"
author = "Mubarak Almehairbi"
description = "Creates user interfaces (websites and desktop apps) from HTML easily"
package_name = "toui"
requirements = []
optional_requirements = ['flask-login', 'flask-sqlalchemy', 'flask-basicauth']

reqs_txt = \
"""
beautifulsoup4==4.12.2
Flask==2.2.5
Flask_BasicAuth==0.2.0
Flask_Caching==2.0.2
Flask_Login==0.6.2
flask_sock==0.6.0
flask_sqlalchemy==3.0.3
pywebview==4.1
tinycss==0.4
"""

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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=[package_name],
    install_requires=requirements
)