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
    toui init
        Creates a basic ToUI project template in the current directory.


    toui --minimal-reqs
        Installs the minimal requirements for ToUI to work. This is useful if you want to
        install the optional requirements manually.

    toui --all-reqs
        Installs all the requirements for ToUI to work. This is useful if you want to
        use all functions in ToUI.

    toui --help
        Displays this help text.
"""
def main():
    pkg_directory = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if "--help" in sys.argv or len(sys.argv) == 1:
        print(help_text)

    try:
        if "--minimal-reqs" in sys.argv:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', "-r", f"{pkg_directory}/requirements.txt"])

        if "--all-reqs" in sys.argv:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', "-r", f"{pkg_directory}/requirements.txt"])
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', "-r", f"{pkg_directory}/optional_requirements.txt"])
    except subprocess.CalledProcessError as e:
        print("An error occured while installing the requirements. Please try again.")
        print(e.output)
    if "init" in sys.argv:
        if not "--full" in sys.argv:
            response = requests.get("https://github.com/mubarakalmehairbi/BasicToUIProject/archive/master.zip", stream=True)
            project_path = "MyBasicToUIProject"
            if os.path.exists(project_path):
                i = 1
                project_path = f"MyBasicToUIProject_{i}"
                while os.path.exists(project_path):
                    i += 1
                    project_path = f"MyBasicToUIProject_{i}"
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extractall(project_path)
            

        else:
            # To be added soon.
            #requests.get("https://github.com/mubarakalmehairbi/ToUIFullAppTemplate/archive/master.zip")
            pass

if __name__ == "__main__":
    main()