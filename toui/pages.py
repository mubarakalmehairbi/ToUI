"""
A module that creates web pages or windows.
"""
import os
import time
from bs4 import BeautifulSoup
import webview
import json
from flask import session
from toui.elements import Element
from toui._javascript_templates import custom_func, get_script
from copy import copy
from toui._helpers import warn, info, debug, selector_to_str, obj_converter
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
        js_kwargs = {"url": kwargs['url'], "new": kwargs['new']}
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}


class Page:
    """
    Creates an HTML page that can be used as a window or as a webpage.

    Attributes
    ----------
    url: str
        The URL of the page.

    title: str
        In desktop app, this attribute will be the title of the window.

    window_defaults: dict
        In desktop apps, this dictionary sets the default parameters of the window. To set a certain default parameter for
        a window before creating it, include it in this dictionary. The parameters that can be set are the keyword arguments
        of the class [`webview.create_window()`](https://pywebview.flowrl.com/guide/api.html) in pywebview package.

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

    def __init__(self, html_file=None, html_str=None, url=None, title=None):
        """
        Parameters
        ----------
        html_file: str
            The path to the HTML file.

        html_str: str
            A string containing HTML code.

        url: str, optional
            If the page was used as a webpage, this will be the URL of the page.

        title: str
            In desktop app, this parameter will be the title of the window.

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
        self.title = title
        self.window_defaults = {}

        # Other internal attributes
        self._app = None
        self._signal_mode = False
        self._signals = []
        self._functions = {}
        self._basic_view_func = lambda: view_func(self)
        self._view_func = self._basic_view_func
        self._uid = None

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.to_str()

    def __copy__(self):
        new_pg = Page(html_file=self._html_file, url=self.url)
        new_pg.from_bs4_soup(self.to_bs4_soup())
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
            If the element was found, an `Element` object will be returned. Otherwise ``None``
            will be returned.

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
            elements_list.append(element)
        return elements_list
    
    def get_element_from_selector(self, selector, do_copy=False):
        """
        Gets an element from its CSS selector.

        Parameters
        ----------
        selector: str

        do_copy: bool, default = False
            If ``True``, the element will be copied.

        Returns
        -------
        element: Element
            If the element was found, an `Element` object will be returned. Otherwise ``None``
            will be returned.

        """
        bs4_tag = self._html.select_one(selector=selector)
        if bs4_tag is None:
            return None
        element = Element()
        if do_copy:
            element.from_bs4_tag(bs4_tag)
        else:
            element._from_bs4_tag_no_copy(bs4_tag)
        element._parent_page = self
        element._signal_mode = self._signal_mode
        return element

    def get_html_element(self) -> Element:
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

    def get_body_element(self) -> Element:
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
        name = func.__name__
        if not callable(func):
            warn(f"Variable '{name}' is not a function.")
            return
        if name.startswith("_"):
            warn(f"Function '{name}' starts with '_'. It is safer to avoid functions that starts with '_'"
                 f"because they might overlap with functions used by the package.")
        if self._func_exists(name):
            warn(f"Function '{name}' exists.")
        old_functions = copy(self._functions)
        self._functions[name] = func
        if func.__name__ in old_functions:
            return ""
        script_element = Element("script")
        script_element.set_content(custom_func(func.__name__))
        self.get_elements(tag_name="html")[0].add_content(script_element)
        return func.__name__

    def on_url_request(self, func, display_return_value=False):
        """
        Sets a function that will be called when the user types the URL in a browser or when a request is sent to the
        URL. You can view it as the `view_func` in Flask. It might have limited functionality compared to calling Python
        functions from HTML, but it is the best for retrieving data from HTTP requests.

        Parameters
        ----------
        func: Callable
            The function that will be called when a request is sent to the URL.

        display_return_value: bool, default=False
            If ``True``, the browser will display the return value of the function when the URL is loaded. If ``False``,
            the return value will be ignored.

        """
        def new_func():
            original_return = self._basic_view_func()
            session['user page'] = copy(self)
            try:
                user_id = self._app._user_vars._get("user-id")
                if user_id:
                    session['_user_id'] = user_id
                new_return = func()
                if display_return_value:
                    del session['user page']
                    return new_return
                else:
                    pg = session['user page']
                    del session['user page']
                    return pg.to_str()
            except Exception as e:
                if 'user page' in session:
                    del session['user page']
                raise e

        self._view_func = new_func

    def get_window(self):
        for window in webview.windows:
            if window.uid == self._uid:
                return window

    def _add_script(self):
        script_tag = Element("script")
        script_content = get_script(self._app.__class__.__name__)
        script_tag.set_content(script_content)
        self.get_elements(tag_name="html")[0].add_content(script_tag)

    def _create_window(self):
        title = self.title
        url = f"http://localhost:{self._app._port}"+self.url
        window_defaults = self.window_defaults.copy()
        for key, value in window_defaults.items():
            if key == "title":
                title = value
                del window_defaults['title']
            if key == "url":
                warn(f"The window will load the URL '{value}' instead of '{self.url}' because it was set in `default_windows`.")
                url = value
                del window_defaults['url']
        window = webview.create_window(title=title, url=url, **window_defaults)
        self._uid = window.uid
        debug(f"UID of window: {self._uid}")
        def get_uid():
            return self._uid
        window.expose(get_uid)
        return window

    def _evaluate_js(self, func, kwargs):
        """This function is currently unused."""
        data_from_js = ""
        def wait_then_get_result(result):
            nonlocal data_from_js
            data_from_js = result
        codejs = f"""
        var kwargs = JSON.parse(\'{json.dumps(kwargs)}\')
        {func}(kwargs)
        """
        debug("EVALUATE: " + codejs)
        self.window.evaluate_js(codejs, callback=wait_then_get_result)
        return data_from_js

    @_PageSignal(app_types=['Website'])
    def _open_another_page(self, url, new):
        if self._app.__class__.__name__ == "DesktopApp":
            if new:
                pg = Page(url=url)
                pg._app = self._app
                return pg._create_window()
            else:
                full_url = f"http://localhost:{self._app._port}" + url
                window = self.get_window()
                window.load_url(full_url)
                return window
            
    def _inherit_functions(self):
        for page in self._app.pages:
            if page.url == self.url:
                self._functions.update(page._functions)
                return
            
    def _get_functions(self):
        """Gets all added functions in this class. This is a private function."""
        return self._functions

    def _func_exists(self, func_name: str):
        """Checks if a function exists. This is a private function."""
        if func_name in self._get_functions().keys():
            return True
        else:
            return False

    def _call_func(self, func_name, *args, page=None):
        """Calls a function in this class. Its return value depends on the function called. This is a private function."""
        functions = self._get_functions()
        info(f'"{func_name}" called')
        return functions[func_name](*args)


if __name__ == "__main__":
    import doctest
    doctest.testmod()