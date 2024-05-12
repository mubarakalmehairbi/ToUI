import subprocess
import sys
import os
import requests
import zipfile
import io

help_text = """
ToUI Command Line Interface
===========================
Usage:
    toui init [--full]
        Creates a basic ToUI project template in the current directory. If --full is
        specified, a full ToUI project template with many features will be created.

    toui --minimal-reqs
        Installs the minimal requirements for ToUI to work. This is useful if you want to
        install the optional requirements manually.

    toui --all-reqs
        Installs all the requirements for ToUI to work. This is useful if you want to
        use all functions in ToUI.

    toui --help
        Displays this help text.
"""
reqs = """beautifulsoup4==4.12.2
Flask==2.2.5
flask_sock==0.6.0
pywebview==4.1
tinycss==0.4
requests==2.31.0"""

optional_reqs = """flask_sqlalchemy==3.0.3
Flask_BasicAuth==0.2.0
Flask_Login==0.6.2
firebase_admin==6.2.0
stripe==5.5.0"""

def install_reqs(reqs):
    for pkg in reqs.splitlines():
        pkg_name = pkg.split("==")[0]
        pkg_version = pkg.split("==")[1]
        pkg_major_version = pkg_version.split(".")[0]
        req = f"{pkg_name}>={pkg_version},<{int(pkg_major_version)+1}"
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])

def main():
    if "--help" in sys.argv or len(sys.argv) == 1:
        print(help_text)

    try:
        if "--minimal-reqs" in sys.argv:
            install_reqs(reqs)

        if "--all-reqs" in sys.argv:
            install_reqs(reqs)
            install_reqs(optional_reqs)
    except subprocess.CalledProcessError as e:
        print("An error occured while installing the requirements. Please try again.")
        print(e.output)
    if "init" in sys.argv:
        if not "--full" in sys.argv:
            response = requests.get("https://github.com/mubarakalmehairbi/BasicToUIProject/archive/master.zip", stream=True)
            project_name = "MyBasicToUIProject"
        else:
            response = requests.get("https://github.com/mubarakalmehairbi/FullToUIProject/archive/master.zip")
            project_name = "MyFullToUIProject"
        project_path = project_name
        if os.path.exists(project_path):
            i = 1
            project_path = f"{project_name}_{i}"
            while os.path.exists(project_path):
                i += 1
                project_path = f"{project_name}_{i}"
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(project_path)

if __name__ == "__main__":
    main()