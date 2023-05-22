"""
A module that creates HTML elements.
"""
from bs4 import BeautifulSoup
from bs4.element import Tag
from copy import copy
import tinycss
from toui._signals import Signal
from toui._helpers import warn, debug, selector_to_str, obj_converter


class _ElementSignal(Signal):
    """
    Creates signals that will be sent to JavaScript.

    These signals are related the methods of the `Element` object.
    """

    @staticmethod
    def _default_kwargs(kwargs):
        original_copy = kwargs['original_copy']
        return {"selector": original_copy.get_unique_selector()}

    @staticmethod
    def from_str(**kwargs):
        js_func = "_replaceElement"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['element'] = kwargs['element_as_str']
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def from_bs4_tag(**kwargs):
        js_func = "_replaceElement"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['element'] = str(kwargs['bs4_tag'])
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def set_attr(**kwargs):
        js_func = "_setAttr"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['name'] = kwargs['name']
        js_kwargs['value'] = str(kwargs['value'])
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def del_attr(**kwargs):
        js_func = "_delAttr"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['name'] = kwargs['name']
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def get_files(**kwargs):
        js_func = "_getFiles"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['with_content'] = kwargs['with_content']
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def set_content(**kwargs):
        js_func = "_setContent"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['content'] = str(kwargs['content'])
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}

    @staticmethod
    def add_content(**kwargs):
        js_func = "_addContent"
        js_args = []
        js_kwargs = _ElementSignal._default_kwargs(kwargs)
        js_kwargs['content'] = str(kwargs['content'])
        return {'func': js_func, 'args': js_args, 'kwargs': js_kwargs}


class Element:
    """
    Creates an HTML element.

    Examples
    --------

    Creating a ``<button>`` HTML element:

    >>> button = Element("button")
    >>> button
    <button></button>

    Setting the inner HTML content of the element:

    >>> button.set_content("Click me")
    >>> button
    <button>Click me</button>

    Setting the element's attributes:

    >>> button.set_attr("name", "button-name")
    >>> button
    <button name="button-name">Click me</button>

    """

    def __init__(self, tag_name="div"):
        self._element = Tag(name=tag_name)
        self._parent_page = None
        self._signal_mode = False
        self._functions = {}

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.to_str()

    @property
    def _app(self):
        return self._parent_page._app

    @_ElementSignal()
    def from_str(self, html_str):
        """
        Converts HTML code to an `Element` object.

        Parameters
        ----------
        html_str: str

        """
        soup = BeautifulSoup(html_str, features="html.parser")
        tags = soup.find_all()
        if len(tags) > 0:
            tag = tags[0]
            self._element = tag
        else:
            warn("No element found in string")

    def to_str(self):
        """
        Converts the `Element` object to HTML code.

        Returns
        -------
        str

        """
        return str(self._element)

    @_ElementSignal()
    def from_bs4_tag(self, bs4_tag):
        """
        Converts a `bs4.element.Tag` object to an `Element` object.

        Parameters
        ----------
        bs4_tag: bs4.element.Tag

        See Also
        --------
        bs4

        """
        self._element = copy(bs4_tag)

    def to_bs4_tag(self):
        """
        Converts the `Element` object to a `bs4.element.Tag` object.

        Returns
        -------
        bs4.element.Tag

        See Also
        --------
        bs4

        """
        return copy(self._element)

    def get_element(self, element_id, do_copy=False):
        """
        Gets a child element from its ``id`` attribute.

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
        bs4_tag = self._element.find(id=element_id)
        element = Element()
        if do_copy:
            element.from_bs4_tag(bs4_tag)
        else:
            element._from_bs4_tag_no_copy(bs4_tag)
        element._signal_mode = self._signal_mode
        element._parent_page = self._parent_page
        return element

    def get_elements(self, tag_name=None, class_name=None, name=None, do_copy=False, attrs=None):
        """
        Get children elements by their tag name and attributes.

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
        elements_list: list(Element)
            A list of `Element` objects that match the parameters.

        """
        if attrs is None:
            attrs = {}
        if class_name:
            attrs['class'] = class_name
        if name:
            attrs['name'] = name
        bs4_tags = self._element.find_all(name=tag_name, attrs=attrs)
        elements_list = []
        for tag_num, bs4_tag in enumerate(bs4_tags):
            element = Element()
            if do_copy:
                element.from_bs4_tag(bs4_tag)
            else:
                element._from_bs4_tag_no_copy(bs4_tag)
            element._signal_mode = self._signal_mode
            element._parent_page = self._parent_page
            elements_list.append(element)
        return elements_list
    
    def get_parent(self, do_copy=False) -> 'Element':
        """
        Gets the parent element.

        Parameters
        ----------
        do_copy: bool, default = False
            If ``True``, the element will be copied.

        Returns
        -------
        element: Element
            If a parent was found, an `Element` object will be returned.

        None
            If a parent was not found.

        """
        bs4_tag = self._element.parent
        if not isinstance(bs4_tag, Tag):
            return None
        element = Element()
        if do_copy:
            element.from_bs4_tag(bs4_tag)
        else:
            element._from_bs4_tag_no_copy(bs4_tag)
        element._signal_mode = self._signal_mode
        element._parent_page = self._parent_page
        return element
    
    def get_selector(self) -> str:
        """
        Gets the CSS selector of an element.

        Returns
        -------
        str

        None:
            If the element is not part of a page.

        """
        selector = self._element.name + ''.join([f'[{attr}="{value}"]' for attr, value in self._element.attrs.items()])
        return selector
    
    def get_unique_selector(self):
        """
        Gets the unique CSS selector of an element.

        Returns
        -------
        str

        None:
            If the element is not part of a page.

        """
        element = self._element
        path = []
        while element is not None and element.name != "[document]":
            selector = element.name.lower()

            if element.get('id'):
                selector += '#' + element['id']
                path.insert(0, selector)
                break
            else:
                index = [child for child in element.parent.children if child.name == element.name].index(element) + 1
                if index != 1:
                    selector += ":nth-of-type(" + str(index) + ")"

            path.insert(0, selector)
            element = element.parent

        return ' > '.join(path)

    def get_attr(self, name):
        """
        Gets the value of an HTML element attribute.

        Parameters
        ----------
        name: str
            The name of the attribute.

        Returns
        -------
        str
         If the attribute exists.

        None
            If the attribute does not exist.

        """
        return self._element.attrs.get(name)

    @_ElementSignal()
    def set_attr(self, name, value):
        """
        Sets the value of an HTML element attribute.

        Parameters
        ----------
        name: str
            The name of the attribute.

        value
            The new value of the attribute.

        """
        value = str(value)
        self._element.attrs[name] = value

    def has_attr(self, name):
        """
        Checks if the HTML element has the specified attribute.

        Parameters
        ----------
        name: str
            The name of the attribute.

        Returns
        -------
        bool

        """
        return self.get_attr(name) != None

    @_ElementSignal()
    def del_attr(self, name):
        """
        Removes an HTML element attribute.

        Parameters
        ----------
        name: str
            The name of the attribute.

        """
        if self.has_attr(name):
            del self._element.attrs[name]

    def get_id(self):
        """
        Gets the ``id`` attribute of the HTML element.

        Returns
        -------
        str
         If the attribute exists.

        None
            If the attribute does not exist.

        """
        return self.get_attr("id")

    def set_id(self, value):
        """
        Sets the value of the ``id`` attribute.

        Parameters
        ----------
        value
            The new value of the ``id`` attribute.

        """
        self.set_attr("id", value)

    def get_value(self):
        """
        Gets the ``value`` attribute of the HTML element.

        Returns
        -------
        str
            If the attribute exists.

        None
            If the attribute does not exist.

        """
        return self.get_attr("value")
    
    def get_selected(self) -> 'Element':
        """
        Gets the selected option of the HTML element ``<select>``.

        This method is used for ``<select>`` elements only.

        Returns
        -------
        Element
            If it has a selected option.

        None
            If it does not have a selected option.

        """
        for element in self.get_elements():
            if element.has_attr("selected"):
                return element

    def set_value(self, value):
        """
        Sets the value of the ``value`` attribute.

        Parameters
        ----------
        value
            The new value of the ``value`` attribute.

        """
        self.set_attr("value", value)

    @_ElementSignal(return_type="js")
    def get_files(self, with_content=False):
        """
        Gets uploaded files from element.

        This method is useful when uploading files using ``<input type="file">`` element.

        Parameters
        ----------
        with_content: bool, default=False
            If ``True``, the contents of the files will be included in the output.

        Returns
        -------
        list(File)
            A list of `File` objects.

        See Also
        --------
        ~toui._signals.File

        """
        return []

    def get_content(self):
        """
        Gets the inner HTML content of the element.

        It is similar to getting the ``Element.innerHTML`` property in JavaScript.

        Returns
        -------
        str

        """
        return self._element.decode_contents()

    @_ElementSignal()
    def set_content(self, content):
        """
        Sets the inner HTML content of the element.

        Parameters
        ----------
        content
            The new inner HTML content.

        """
        self._element.clear()
        self._manage_content_functions(content)
        content = str(content)
        content = BeautifulSoup(content, features="html.parser")
        self._element.append(content)

    @_ElementSignal()
    def add_content(self, content):
        """
        Adds to the inner HTML content of the element.

        Parameters
        ----------
        content
            The added inner HTML content.

        """
        self._manage_content_functions(content)
        content = str(content)
        content = BeautifulSoup(content, features="html.parser")
        self._element.append(content)

    def get_style_property(self, property):
        """
        Gets the value of a CSS property inside the ``style`` attribute.

        Parameters
        ----------
        property: str
            The name of the property

        Returns
        -------
        str

        """
        if not self.has_attr("style"):
            return
        style = self.get_attr('style')
        parser = tinycss.make_parser("page3")
        declarations = parser.parse_style_attr(style)[0]
        for declaration in declarations:
            if declaration.name == property:
                property_value = ""
                for v in declaration.value:
                    property_value += v.as_css()
                return property_value

    def set_style_property(self, property, value):
        """
        Sets the value of a CSS property inside the ``style`` attribute.

        Parameters
        ----------
        property: str
            The name of the property

        value: str
            The new value of the property.

        """
        if self.has_attr("style"):
            style = self.get_attr('style')
        else:
            style = ""
        parser = tinycss.make_parser("page3")
        declarations = parser.parse_style_attr(style)[0]
        property_is_set = False
        new_style = ""
        for declaration in declarations:
            new_style += declaration.name + ": "
            if declaration.name == property:
                property_value = value
                property_is_set = True
            else:
                property_value = ""
                for v in declaration.value:
                    property_value += v.as_css()
            new_style += f"{property_value};"
        if not property_is_set:
            new_style += f"{property}: {value};"
        self.set_attr(name="style", value=new_style)

    def get_width_property(self):
        """
        Gets the value of the CSS property `width` inside the ``style`` attribute.

        Returns
        -------
        str

        """
        return self.get_style_property("width")

    def set_width_property(self, value):
        """
        Sets the value of the CSS property `width` inside the ``style`` attribute.

        Parameters
        ----------
        value: str

        """
        self.set_style_property("width", value)

    def get_height_property(self):
        """
        Gets the value of the CSS property `height` inside the ``style`` attribute.

        Returns
        -------
        str

        """
        return self.get_style_property("height")

    def set_height_property(self, value):
        """
        Sets the value of the CSS property `height` inside the ``style`` attribute.

        Parameters
        ----------
        value: str

        """
        self.set_style_property("height", value)

    def _manage_content_functions(self, content):
        if type(content) is Element:
            for func in content._functions.values():
                if self._parent_page:
                    self._parent_page.add_function(func)
                else:
                    self._functions[func.__name__] = func

    def on(self, event, func_or_name, *func_args, quotes=True, return_itself=False):
        """
        Creates an HTML event attribute and adds a Python function to it.

        If you want to add JavaScript code instead of a single function, use `Element.set_attr` method
        instead.

        Parameters
        ----------
        event: str
            Can be any HTML event, but without the "on" prefix.
            For example: `click`, `load`, `mouseover`, etc.

        func_or_name: Callable or str
            The Python function to be called when the event is triggered. If the Python function
            itself is added, the function will be automatically added to the parent `Page`. However,
            if the function name is added, you need to add the Python function itself to the
            parent `Page` manually using the method `Page.add_function`.
            The `func_or_name` parameter can also be a JavaScript function. In this case, there is
            no need to use the method `Page.add_function`.

        func_args
            The arguments of the function. Each argument will be automatically converted to a
            string.

        quotes: bool, default = True
            If ``True``, each argument will be surrounded by double quotes.

        return_itsef: bool, default=False
            If ``True``, the first argument of the function will be the element itself.

        Examples
        --------

        Adding a function to a button:

        >>> def printValueType(value):
        ...     value_type = type(value)
        ...     print(value_type)
        >>> button = Element("button")
        >>> button.on("click", printValue, 10)

        This function prints the type of the first argument.
        If the button was clicked, the output will be:

        >>> #<class 'str'>

        The value ``10`` was converted to a string because the parameter `quotes` was ``True``.
        However, if we change the `quotes` to ``False``:

        >>> def printValueType(value):
        ...     value_type = type(value)
        ...     print(value_type)
        >>> button = Element("button")
        >>> button.on("click", printValue, 10, quotes=False)

        The output will be:

        >>> #<class 'int'>

        """
        if quotes:
            args = ",".join([f'"{arg}"' for arg in func_args])
        else:
            args = ",".join([f'{obj_converter(arg)}' for arg in func_args])
        if return_itself:
            args = "this, " + args
        if callable(func_or_name):
            name = func_or_name.__name__
            if self._parent_page:
                self._parent_page.add_function(func_or_name)
            else:
                self._functions[func_or_name.__name__] = func_or_name
        else:
            name = func_or_name
        value = f"{name}({args})"
        self.set_attr(name=f"on{event}", value=value)

    def onclick(self, func_or_name, *func_args, quotes=True, return_itself=False):
        """
        Creates the HTML event attribute ``onclick`` and adds a Python function to it.

        If you want to add JavaScript code instead of a single function, use `Element.set_attr` method
        instead.

        Parameters
        ----------
        func_or_name: Callable or str
            The Python function to be called when the event is triggered. If the Python function
            itself is added, the function will be automatically added to the parent `Page`. However,
            if the function name is added, you need to add the Python function itself to the
            parent `Page` manually using the method `Page.add_function`.
            The `func_or_name` parameter can also be a JavaScript function. In this case, there is
            no need to use the method `Page.add_function`.

        func_args
            The arguments of the function. Each argument will be automatically converted to a
            string.

        quotes: bool, default = True
            If ``True``, each argument will be surrounded by double quotes.

        return_itsef: bool, default=False
            If ``True``, the first argument of the function will be the element itself.

        See Also
        --------
        Element.on

        """
        self.on('click', func_or_name, *func_args, quotes=quotes, return_itself=return_itself)

    def _from_bs4_tag_no_copy(self, bs4_tag):
        self._element = bs4_tag


class IFrameElement(Element):
    """
    An ``<iframe>`` element edited to fit the content within it.
    """
    def __init__(self, src=None, borderless=True):
        """
        Parameters
        ----------
        src: str
            The ``src`` attribute of the element.

        borderless: bool, default = True
            If ``True``, the border will be removed from the element.

        """
        super().__init__(tag_name="iframe")
        if borderless:
            self.set_style_property("border", "none")
        self.set_attr("marginwidth", "0")
        self.set_attr("marginheight", "0")
        self.set_attr("align", "center")
        self.on('load', '_resizeEmbed', "this", quotes=False)
        if src:
            self.set_attr("src", src)


if __name__ == "__main__":
    import doctest
    results = doctest.testmod()
    print(results)