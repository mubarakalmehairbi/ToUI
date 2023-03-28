"""
A module that creates web pages or windows.
"""
import os
import time
from bs4 import BeautifulSoup
import webview
import json
from toui.elements import Element
from toui._javascript_templates import custom_func, get_script
from copy import copy
from toui._helpers import warn, info, debug, selector_to_str
from toui._signals import Signal
from toui._defaults import view_func


class _PageSignal(Signal):
    """
    Creates signals that will be sent to JavaScript.

    These signals are related the methods of the `Page` object.
    """

    no_return_functions = ["add_function"]

    @staticmethod
    def from_str(**kwargs):
        js_func = "_setDoc"
        js_args = []
        js_kwargs = {"doc": kwargs['html_str']}
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def from_bs4_soup(**kwargs):
        js_func = "_setDoc"
        js_args = []
        js_kwargs = {"doc": str(kwargs['bs4_soup'])}
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def add_function(**kwargs):
        value = kwargs['return_value']
        if value != "":
            value = custom_func(value)
        js_func = "_addScript"
        js_args = []
        js_kwargs = {"script": value}
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def _open_another_page(**kwargs):
        js_func = "_goTo"
        js_args = []
        js_kwargs = {"url": kwargs['url']}
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}


class Page:
    """
    Creates an HTML page that can be used as a window or as a webpage.

    Attributes
    ----------
    url: str
        The URL of the page.

    window: pywebview.Window, default = None
        A `pywebview.Window` object. It is automatically created when adding the `Page` to
        `DesktopApp` and running the app.

    view_func: Callable
        The view function of the `Page`. This is the function that will be decorated by
        `Flask.route()` in when creating web apps.

    Examples
    --------

    Importing the class:

    >>> from toui import Page

    Creating a `Page` from an HTML file:

    >>> path = "../examples/assets/test1.html"
    >>> page = Page(html_file=path)

    Creating a `Page` from a string:

    >>> page = Page(html_str="<html><h1>Hello</h1></html>")
    >>> page
    <html><h1>Hello</h1></html>

    Creating a page with a URL:

    >>> page = Page(html_str="<html><h1>Hello</h1></html>", url="/")

    Getting an element in the `Page` from its id:

    >>> page = Page(html_str='<html><h1 id="heading">Hello</h1></html>', url="/")
    >>> element = page.get_element(element_id="heading")
    >>> element
    <h1 id="heading">Hello</h1>

    See Also
    --------
    `pywebview api`: https://pywebview.flowrl.com/guide/api.html

    """

    def __init__(self, html_file=None, html_str=None, url=None):
        """
        Parameters
        ----------
        html_file: str
            The path to the HTML file.

        html_str: str
            A string containing HTML code.

        url: str, optional
            If the page was used as a webpage, this will be the URL of the page.

        """
        if html_file:
            self._html_file = html_file
            with open(html_file, "rt") as file:
                original_html = file.read()
            if url is None:
                url = "/" + os.path.basename(html_file)
        elif html_str:
            original_html = html_str
            self._html_file = None
        else:
            original_html = "<html></html>"
            self._html_file = None
        self._html = BeautifulSoup(original_html, features="html.parser")
        if self._html.find("html") is None:
            self._html = BeautifulSoup(f"<html>{original_html}</html>", features="html.parser")
        if url is None:
            url = "/"
        self.url = url

        # Other attributes
        self.window = None

        # Other internal attributes
        self._app = None
        self._signal_mode = False
        self._signals = []
        self._functions = {}
        self._view_func = lambda: view_func(self)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.to_str()

    def __copy__(self):
        new_pg = Page(html_file=self._html_file, url=self.url)
        new_pg.from_bs4_soup(self.to_bs4_soup())
        new_pg.window = copy(self.window)
        new_pg._signal_mode = self._signal_mode
        new_pg._app = self._app
        return new_pg
    
    @_PageSignal()
    def from_str(self, html_str):
        """
        Converts HTML code to a `Page` object.

        Parameters
        ----------
        html_str: str
            HTML code.

        """
        self._html = BeautifulSoup(html_str, features="html.parser")

    def to_str(self):
        """
        Converts the `Page` object to HTML code.

        Returns
        -------
        str

        """
        return str(self._html)

    def from_html_file(self, html_path):
        """
        Reads an HTML file and converts it to an `Page` object.

        Parameters
        ----------
        html_path: str

        """
        with open(html_path, "rt") as file:
            self.from_str(file.read())

    def to_html_file(self, html_path):
        """
        Converts the `Page` object to an HTML file.

        Parameters
        ----------
        html_path: str

        """
        with open(html_path, "w") as file:
            file.write(self.to_str())

    @_PageSignal()
    def from_bs4_soup(self, bs4_soup):
        """
        Converts a `bs4.BeautifulSoap` object to a `Page` object.
        The `bs4.BeautifulSoap` object will be copied before converting.

        Parameters
        ----------
        bs4_soup: bs4.BeautifulSoap

        See Also
        --------
        bs4

        """
        self._html = copy(bs4_soup)

    def to_bs4_soup(self):
        """
        Converts the `Page` object to a `bs4.BeautifulSoap` object.
        The `Page` object will be copied before converting.

        Returns
        -------
        bs4.BeautifulSoap

        See Also
        --------
        bs4: https://beautiful-soup-4.readthedocs.io/en/latest/

        """
        return copy(self._html)

    def get_element(self, element_id, do_copy=False):
        """
        Gets an element from its ``id`` attribute. You can imagine this function as ``document.getElementById``
        in JavaScript.

        Creating a page and getting an element by its ``id``:

        >>> page = Page(html_str='<html><h1 id="heading">Hello</h1></html>', url="/")
        >>> element = page.get_element(element_id="heading")
        >>> element
        <h1 id="heading">Hello</h1>

        Parameters
        ----------
        element_id: str

        do_copy: bool, default = False
            If ``True``, the element will be copied.

        Returns
        -------
        element: Element
            If the element was found, an `Element` object will be returned.

        None
            If the element was not found.

        """
        bs4_tag = self._html.find(id=element_id)
        if bs4_tag is None:
            return None
        element = Element()
        if do_copy:
            element.from_bs4_tag(bs4_tag)
        else:
            element._from_bs4_tag_no_copy(bs4_tag)
        element._parent_page = self
        element._signal_mode = self._signal_mode
        element._selector = {"selector": f"[id={element_id}]"}
        return element

    def get_elements(self, tag_name=None, class_name=None, name=None, do_copy=False, attrs=None):
        """
        Get elements from the `Page` by their tag name and attributes.

        Parameters
        ----------
        tag_name: str, default=None
            The tag name of the elements.

        class_name: str, default=None
            The value of the ``class`` attribute of the elements.

        name: str, default=None
            The value of the ``name`` attribute of the elements.

        do_copy: bool
            If ``True``, the elements will be copied.

        attrs: dict, default=None
            Attributes other than ``class`` and ``name`` can be specified in this dictionary.

        Returns
        -------
        elements_list: List
            A list of `Element` objects that match the parameters.

        """
        if attrs is None:
            attrs = {}
        if class_name:
            attrs['class'] = class_name
        if name:
            attrs['name'] = name
        bs4_tags = self._html.find_all(name=tag_name, attrs=attrs)
        elements_list = []
        for tag_num, bs4_tag in enumerate(bs4_tags):
            element = Element()
            if do_copy:
                element.from_bs4_tag(bs4_tag)
            else:
                element._from_bs4_tag_no_copy(bs4_tag)
            element._parent_page = self
            element._signal_mode = self._signal_mode
            element._selector = {"selector": selector_to_str(tag_name=tag_name, class_name=class_name,
                                                             name=name, attrs=attrs),
                                 "number": tag_num}
            elements_list.append(element)
        return elements_list

    def get_html_element(self):
        """
        Gets the first ``<html>`` element.

        Returns
        -------
        Element

        None
            If the ``<html>`` element was not found.

        """
        elements = self.get_elements("html")
        if len(elements) > 0:
            return elements[0]

    def get_body_element(self):
        """
        Gets the first ``<body>`` element.

        Returns
        -------
        Element

        None
            If the ``<body>`` element was not found.

        """
        elements = self.get_elements("body")
        if len(elements) > 0:
            return elements[0]

    @_PageSignal()
    def add_function(self, func):
        """
        Adds a function to the `Page`. This function can be called from an HTML element.

        Examples
        --------

        Consider an HTML code that contains the following:

        >>> html_with_function = '<html><button onclick="printValue()">Print</button></html>'

        Notice that the ``<button>`` element contains the attribute ``onclick`` calling a Python function `printValue`.
        However, this function is not yet added to the HTML page. To add the function, define it in Python and add it
        to a `Page`:

        >>> def printValue():
        ...     print("value")
        >>> page = Page(html_str=html_with_function)
        >>> page.add_function(printValue)

        Now create a `Website` and add the `Page` to it:

        >>> from toui import Website
        >>> app = Website()
        >>> app.add_pages(page)

        Parameters
        ----------
        function
            Function to be added to the page.

        Returns
        -------
        None

        """
        if self._app:
            self._app._add_function(func)
        old_functions = copy(self._functions)
        self._functions[func.__name__] = func
        if func.__name__ in old_functions:
            return ""
        script_element = Element("script")
        script_element.set_content(custom_func(func.__name__))
        self.get_elements(tag_name="html")[0].add_content(script_element)
        return func.__name__

    @property
    def view_func(self):
        return self._view_func

    @view_func.setter
    def view_func(self, func):
        self._view_func = lambda: func(self)

    def _add_script(self, template_type="web"):
        script_tag = Element("script")
        script_content = get_script(template_type)
        script_tag.set_content(script_content)
        self.get_elements(tag_name="html")[0].add_content(script_tag)

    def _create_window(self, name, api, assets_folder):
        with _TempHTML(directory=assets_folder, html=self.to_str(),
                       win_kwargs={"title": name, "js_api": api}) as temp_html:
            self.window = temp_html.win
            time.sleep(1)
        api.window = self.window
        return self.window

    def _create_first_window(self, name, api, assets_folder):
        self.window = webview.create_window(title=name, js_api=api)
        def func():
            with _TempHTML(directory=assets_folder, html=self.to_str(),
                           win=self.window) as temp_html:
                time.sleep(1)
        api.window = self.window
        return func

    def _evaluate_js(self, func, kwargs):
        codejs = f"""
        var kwargs = JSON.parse(\'{json.dumps(kwargs)}\')
        {func}(kwargs)
        """
        debug("EVALUATE: " + codejs)
        out = self.window.evaluate_js(codejs)

    @_PageSignal()
    def _open_another_page(self, url):
        return


class _TempHTML:

    def __init__(self, directory, win=None, html="", win_args=(), win_kwargs=None):
        self.directory = directory
        self.win = win
        self.html = html
        self.win_args = win_args
        if win_kwargs is None:
            win_kwargs = {}
        self.win_kwargs = win_kwargs

    def __enter__(self):
        i = ""
        name = f"~toui{i}.html"
        while os.path.exists(f"{self.directory}/{name}"):
            if i == "":
                i = 1
            else:
                i += 1
            name = f"~toui{i}.html"
        self.file = f"{self.directory}/{name}"
        file = open(self.file, "w")
        if self.win:
            self.win.load_url(self.file)
        else:
            self.win = webview.create_window(*self.win_args, **self.win_kwargs, url=self.file)
        file.write(self.html)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.file)


if __name__ == "__main__":
    import doctest
    doctest.testmod()