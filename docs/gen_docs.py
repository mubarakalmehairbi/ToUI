import glob
import os
import shutil
import subprocess
import sys
sys.path.append("..")
from toui import Website, DesktopApp, Page, Element, IFrameElement,\
    ToUIBlueprint, quick_website, quick_desktop_app, set_global_app, get_global_app, __version__
from toui._signals import File
from docs.rst_objects import Index, Section, MD, Class, Example, Function

clear = True
run = True

if clear:
    for file in glob.glob("*.rst"):
        if not "template.rst" in file:
            os.remove(file)

classes = []
for cls in (Website, DesktopApp, Page, Element):
    cls_object = Class(cls)
    cls_object.to_rst()
    classes.append(cls_object)

other_objects = []
for cls in (IFrameElement, File):
    cls_object = Class(cls)
    cls_object.to_rst()
    other_objects.append(cls_object)
cls_object = Class(ToUIBlueprint)
cls_object.no_inherit_methods = True
cls_object.to_rst()
other_objects.append(cls_object)

functions = []
for func in (quick_website, quick_desktop_app, set_global_app, get_global_app):
    func_object = Function(func)
    func_object.to_rst()
    functions.append(func_object)

examples = []
examples_paths = [p for p in glob.glob("../examples/*.py") if not os.path.basename(p).startswith("_")]
for example in examples_paths:
    example_object = Example(path=example)
    example_object.to_rst()
    examples.append(example_object)


sections = []
section_api = Section(title="API Reference", autosummary=True, heading="Main classes", children=classes,
                  text="Here you can find the classes you can use in this package.")
section_api.to_rst()

section_api.heading = "Other classes"
section_api.children = [cls for cls in other_objects]
section_api.add_rst()

section_api.heading = "Functions"
section_api.children = [func for func in functions]
section_api.add_rst()

sections.append(section_api)

basic_examples = [e for e in examples if not os.path.basename(e.path).startswith("advanced")]
section_examples = Section(title="Examples", heading="Basic examples", children=[e for e in examples],
                           text="Below you can find some examples of using the package. Some of "
                                "the examples use files inside a folder called 'assets'. To access "
                                "this folder, click on this `link <https://github.com/mubarakalmehairbi/ToUI/tree/main/examples>`_.")
section_examples.to_rst()

section_examples.heading = "Advanced examples"
section_examples.children = [e for e in examples if os.path.basename(e.path).startswith("advanced")]
section_examples.add_rst()

sections.append(section_examples)

section_md = MD(file="how_it_works")
sections.append(section_md)

if os.path.exists("CONTRIBUTING.md"):
    os.remove("CONTRIBUTING.md")
shutil.copyfile("../CONTRIBUTING.md", "CONTRIBUTING.md")
section_md = MD(file="CONTRIBUTING")
sections.append(section_md)

index = Index(package_title="ToUI", readme_path="../README.md", sections=sections, version_text=f"Version: {__version__}")
index.to_rst()


if run:
    subprocess.check_call(['.\make', 'clean'])
    subprocess.check_call(['.\make', 'html'])
