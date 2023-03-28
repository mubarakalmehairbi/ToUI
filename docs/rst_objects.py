import ast
import inspect
import os
from dataclasses import dataclass, field



@dataclass
class Index:

    package_title: str
    sections: list
    version_text: str = ""
    readme_path: str = None

    def to_rst(self):
        index_dict = {"title": self.package_title,
                      "under_title": len(self.package_title) * "=",
                      "version": self.version_text,
                      "contents": "\n   ".join([s.original_title for s in self.sections])}
        if self.readme_path:
            index_dict['read_me'] = f".. include:: {self.readme_path}\n   :parser: myst_parser.sphinx_\n   :end-before: # Documentation"
        else:
            index_dict['read_me'] = ""
        replace_template(index_dict, "index_template.txt", "index.rst")


@dataclass
class Section:

    children: list = field(default_factory=list)

    autosummary: bool = False

    title: str = ""
    text: str = ""
    heading: str = ""

    def to_rst(self):
        self.original_title = self.title
        children = [c.rst for c in self.children]
        contents = "\n   ".join(children)
        text = self.text
        if self.autosummary:
            toc = ".. autosummary::\n   :nosignatures:\n   :toctree:"
        else:
            toc = ".. toctree::\n   :maxdepth: 1"
        section_dict = {"title": self.title,
                        "heading": self.heading,
                        "under_heading": len(self.heading) * "-",
                        "under_title": len(self.title) * "=",
                        "text": text,
                        "toc": toc,
                        "contents": contents}
        replace_template(section_dict, "section_template.txt", f"{self.title}.rst")

    def add_rst(self):
        children = [c.rst for c in self.children]
        contents = "\n   ".join(children)
        if self.autosummary:
            toc = ".. autosummary::\n   :nosignatures:\n   :toctree:"
        else:
            toc = ".. toctree::\n   :maxdepth: 1"
        section_dict = {"title": "",
                        "under_title": "",
                        "heading": self.heading,
                        "under_heading": len(self.heading) * "-",
                        "text": "",
                        "toc": toc,
                        "contents": contents}
        text = replace_template(section_dict, "section_template.txt")
        with open(f"{self.original_title}.rst", "a") as file:
            file.write("\n")
            file.write(text)


class MD:

    def __init__(self, file):
        self.file = self.original_title = file


class Class:

    no_inherit_methods = False

    def __init__(self, cls):
        self.cls = cls
        self.cls_api = f"{self.cls.__module__}.{self.cls.__name__}"
        self.title = self.cls.__name__
        self.rst = self.cls_api

    def to_rst(self):
        cls_api = f"{self.cls.__module__}.{self.cls.__name__}"
        methods = [f for f in inspect.getmembers(self.cls, inspect.isfunction) if not f[0].startswith("_")]
        if self.no_inherit_methods:
            methods = [m for m in methods if not hasattr(self.cls.__bases__[0], m[0])]
        methods_str = "\n   ".join([f"{cls_api}.{m[0]}" for m in methods])
        cls_dict = {"class_name": self.cls.__name__,
                    "under_class_name": "=" * len(self.cls.__name__),
                    "to_class": cls_api,
                    "methods": f"{methods_str}"}
        if methods != []:
            replace_template(cls_dict, "class_template.txt", f"{cls_api}.rst")
        else:
            replace_template(cls_dict, "class_methodless_template.txt", f"{cls_api}.rst")
        for method_name, method in methods:
            method_api = f"{cls_api}.{method_name}"
            method_dict = {"method_name": f"{self.cls.__name__}.{method_name}",
                           "under_method_name": "-" * len(f"{self.cls.__name__}.{method_name}"),
                           "to_method": method_api}
            replace_template(method_dict, "method_template.txt", f"{method_api}.rst")


class Function:

    def __init__(self, func):
        self.func = func
        self.func_api = f"{self.func.__module__}.{self.func.__name__}"
        self.title = self.func.__name__
        self.rst = self.func_api

    def to_rst(self):
        func_dict = {"func_name": self.func.__name__,
                    "under_func_name": "=" * len(self.func.__name__),
                    "to_func": self.func_api}
        replace_template(func_dict, "function_template.txt", f"{self.func_api}.rst")


class Example:

    title: str = None
    path: str
    text: str = None

    def __init__(self, path, title=None, text=None):
        with open(path, "rt") as file:
            content = file.read()
            module = ast.parse(content, type_comments=True)
        docstring = ast.get_docstring(module).strip().splitlines()
        docstring_line_0 = docstring[0]
        self.path = path
        if title:
            self.title = title
        else:
            self.title = docstring_line_0
        if text:
            self.text = text
        else:
            self.text = "\n".join(docstring[1:]).strip()
        self.code = ""
        starting_line_num = module.body[1].lineno - 1
        lines = content.splitlines()
        for line in lines[starting_line_num:]:
            self.code += line + "\n" + "   "

    def to_rst(self):
        self.rst = f"Examples.{os.path.basename(self.path).removesuffix('.py')}"
        example_dict = {"title": self.title,
                        "under_title": len(self.title) * "=",
                        "code": self.code,
                        "text": self.text,
                        "path": self.path}
        replace_template(example_dict, "code_template.txt", f"{self.rst}.rst")


def replace_template(dictionary, rst_template, new_rst_file=None):
    with open("_my_templates/" + rst_template, "rt") as template:
        text = template.read()
        for key, value in dictionary.items():
            text = text.replace("{{" + key + "}}", value)
    if new_rst_file:
        with open(new_rst_file, "w") as new_file:
            print(f"WRITING: {new_rst_file}")
            new_file.write(text)
    return text