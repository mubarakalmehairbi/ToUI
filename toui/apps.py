"""
A module that creates web apps and desktop apps.
"""
import __main__
from flask import Flask, session, request, send_file
from flask_sock import Sock
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
import webview
import json
import inspect
import time
import os
from copy import copy
from abc import ABCMeta, abstractmethod
from toui._helpers import warn, info, debug, error
from toui.pages import Page
from toui.exceptions import ToUIWrongPlaceException
from toui._defaults import validate_ws, validate_data


class _App(metaclass=ABCMeta):
    """The base class for DesktopApp and Website"""

    def _add_function(self, func):
        name = func.__name__
        if not callable(func):
            warn(f"Variable '{name}' is not a function.")
            return
        if name.startswith("_"):
            warn(f"Function '{name}' starts with '_'. It is safer to avoid functions that starts with '_'"
                 f"because they might overlap with functions used by the package.")
        if self._func_exists(name):
            warn(f"Function '{name}' exists.")
        self._functions[name] = func

    @abstractmethod
    def add_pages(self): pass

    @abstractmethod
    def open_new_page(self, url): pass

    @abstractmethod
    def get_user_page(self): pass

    @abstractmethod
    def user_vars(self): pass

    @abstractmethod
    def _communicate(self): pass

    @abstractmethod
    def run(self): pass

    def _add_functions(self, *functions):
        for func in functions:
            self._add_function(func)

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
        if page:
            func = _FuncWithPage(functions[func_name], page)
            return func(*args)
        return functions[func_name](*args)


class _FuncWithPage:
    def __init__(self, func, page):
        self.func = func
        self.page = page
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

        
class Website(_App):
    """
    A class that creates a web application from HTML files.

    Attributes
    ----------
    flask_app: Flask
        ToUI creates web applications using `Flask`. You can access the `Flask` object using the attribute `flask_app`.

    forbidden_urls: list
        These are URLs that ToUI does not allow the user to use because ToUI uses them.

    user_vars: dict
        A dictionary that stores data unique to each user. The data are stored in a `flask` `session` object.

    pages: list
        A list of added `Page` objects.

    Examples
    --------

    Creating a web app:

    >>> from toui import Website
    >>> app = Website(__name__, secret_key="some key")

    Creating a page and adding it to the app:

    >>> from toui import Page
    >>> home_page = Page(html_str="<h1>This is the home page</h1>")
    >>> app.add_pages(home_page)

    Running the app:

    >>> if __name__ == "__main__":
    ...     app.run(debug=True) # doctest: +SKIP

    See Also
    --------
    :py:class:`toui.pages.Page`
    :py:class:`DesktopApp`

    """
    
    def __init__(self, name=None, assets_folder=None, secret_key=None):
        """

        Parameters
        ----------
        name: str (optional)
            The name of the app.

        assets_folder: str (optional)
            The path to the folder that contains the HTML files and other assets.

        secret_key: str (optional)
            Sets the `secret_key` attribute for `flask.Flask`

        """
        self._functions = {}
        if not name:
            if hasattr(__main__, "__file__"):
                name = os.path.basename(__main__.__file__).split(".")[0]
            else:
                name = "app"
        if not assets_folder:
            assets_folder = "/"
        self.flask_app = Flask(name, static_folder=assets_folder, static_url_path="/")
        if secret_key is None:
            warn("No secret key was set. Generating a random secret key for Flask.")
            secret_key = os.urandom(50)
        self.flask_app.secret_key = secret_key
        self.pages = []
        self._socket = Sock(self.flask_app)
        self._socket.route("/toui-communicate")(self._communicate)
        self.flask_app.route("/toui-download", methods=['POST', 'GET'])(self._download)

        self.forbidden_urls = ['/toui-communicate', "/toui-download"]
        self._validate_ws = validate_ws
        self._validate_data = validate_data
        self._auth = None
        self._default_vars = {}
        self._user_cls = None

    def add_pages(self, *pages, do_copy=False, blueprint=None, endpoint=None):
        """
        Adds pages to the app.

        Parameters
        ----------
        pages: list(Page)
            List of `Page` objects.

        do_copy: bool, default = False
            If ``True``, the `Page` will be copied before adding to the app.

        blueprint: toui.structure.ToUIBlueprint, flask.Blueprint, default = None
            If a `flask.Blueprint` or a `ToUIBlueprint` was added, the `Page` view_func will be added
            to the blueprint instead of the `Flask` app.

        endpoint
            `endpoint` parameter in `flask.Flask.route`. If ``None``, the endpoint will be set
            as the unique id of the `Page`. The unique id is obtained through the ``id()``
            function and converted to a string.
            
        """
        for page in pages:
            if page.url in self.forbidden_urls:
                warn(f"The URL '{page.url}' is not allowed and might cause errors.")
            if do_copy:
                page = copy(page)
            page._add_script()
            page._app = self
            self.pages.append(page)
            view_func = page._view_func
            if self._auth:
                view_func = self._auth.required(view_func)
            if not endpoint:
                endpoint_ = str(id(page))
            else:
                endpoint_ = endpoint
            if blueprint:
                route = blueprint.route(page.url, methods=['GET', 'POST'], endpoint=endpoint_)(view_func)
            else:
                route = self.flask_app.route(page.url, methods=['GET', 'POST'], endpoint=endpoint_)(view_func)
            for func in page._functions.values():
                self._add_functions(func)

    def open_new_page(self, url):
        """
        Redirects to another URL.

        This function should only be called after the app starts running.

        Parameters
        ----------
        url: str
            URL of the new page.

        Returns
        -------
        None

        """
        try:
            session.keys()
            self.get_user_page()._open_another_page(url)
        except RuntimeError:
            raise ToUIWrongPlaceException(f"The function `{inspect.currentframe().f_code.co_name}` should only be called after the app runs.")

    def get_user_page(self):
        """
        Returns the current `Page`.

        This function should only be called after the app starts running.

        Returns
        -------
        pg: Page

        """
        try:
            pg = session['user page']
            return pg
        except RuntimeError as e:
            raise ToUIWrongPlaceException(f"The function `{inspect.currentframe().f_code.co_name}` should only be called after the app runs.")

    def run(self, *args, **kwargs):
        """
        Runs the app. It calls the function `flask.Flask.run`. The arguments will be passed to
        `flask.Flask.run` function.

        Parameters
        ----------
        args: Any

        kwargs: Any

        """
        self.flask_app.run(*args, **kwargs)

    @property
    def user_vars(self):
        session_exists = self._session_check()
        if session_exists:
            return session['variables']
        else:
            return self._default_vars

    def _session_check(self):
        """This is a private function."""
        try:
            session.keys()
        except RuntimeError as e:
            return False
        if not "variables" in session.keys():
            debug(f"CREATING SESSION VARIABLES. DEFAULT={self._default_vars}")
            session['variables'] = self._default_vars.copy()
        if not "user page" in session.keys():
            session['user page'] = None
        if not "toui-download" in session.keys():
            session['toui-download'] = None
        return True

    def _communicate(self, ws):
        """This is a private function."""
        validation = self._validate_ws(ws)
        if not validation:
            info("WebSocket validation returns `False`. No data should be sent or received.")
            return
        info(f'WebSocket connected: {ws.connected}')
        while True:
            data_from_js = ws.receive()
            data_validation = self._validate_data(data_from_js)
            if not data_validation:
                info("Data validation returns `False`. The data will not be used.")
                continue
            s = time.time()
            self._session_check()
            data_dict = json.loads(data_from_js)
            func = data_dict['func']
            args = data_dict['args']
            url = data_dict['url']
            new_html = data_dict['html']
            new_page = Page(url=url)
            new_page.from_str(new_html)
            new_page._app = self
            new_page._signal_mode = True
            new_page._ws = ws
            session['user page'] = new_page
            if self._func_exists(func):
                self._call_func(func, *args)
            del session['user page']
            e = time.time()
            debug(f"TIME: {e - s}s")

    def _download(self):
        debug(session.keys())
        file_to_download = session['toui-download']
        debug(f"File to download: {session['toui-download']}")
        if file_to_download:
            return send_file(file_to_download, as_attachment=True)

    def download(self, filepath):
        session['toui-download'] = filepath
        debug(session.keys())
        debug(session['toui-download'])
        #self.open_new_page("/toui-download")

    def create_user_database(self, database_uri):
        """
        Connects to a database that has data specific to each user.

        The database is a table that contains the following columns: `username`, `password`, and `id`.

        Parameters
        ----------
        database_uri

        Returns
        -------

        """
        self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        self._db = SQLAlchemy(self.flask_app)
        self._login_manager = LoginManager(self.flask_app)
        self._load_user = self._login_manager.user_loader(self._load_user)
        class User(UserMixin, self._db.Model):
            __tablename__ = "user"

            id = self._db.Column(self._db.Integer, primary_key=True)
            username = self._db.Column(self._db.String(80), unique=True, nullable=False)
            password = self._db.Column(self._db.String(300), nullable=False, unique=True)

            def __repr__(self):
                return f'<User {self.username}>'
        self._user_cls = User
        with self.flask_app.app_context():
            self._db.create_all()

    def _load_user(self, user_id):
        return self._user_cls.get(int(user_id))

    # Website-specific methods
    @staticmethod
    def get_request():
        """
        Gets data sent from client using HTTP request.

        This method returns the `request` object of `Flask`. The `request` object has some useful attributes such as
        `request.files` which retrieves uploaded files.

        Examples
        --------
        To use this method, first create the app and a page:

        >>> app = Website(__name__, secret_key="some key")
        >>> home_page = Page(html_str=\"\"\"<form method="post" enctype="multipart/form-data">
        ...                              <input type="file" name="filename">
        ...                              <input type="submit">
        ...                              </form>\"\"\", url="/")

        Then create a function that will be called when an HTTP request is made:

        >>> def request_function():
        ...     request = app.get_request()
        ...     print(request.files)

        Now add the function to `Page.on_url_request()` method:

        >>> home_page.on_url_request(request_function)

        Add the page to the app and run the app:

        >>> app.add_pages(home_page)
        >>> if __name__ == "__main__":
        ...     app.run() # doctest: +SKIP

        Returns
        -------
        flask.request

        See Also
        --------
        flask.request
            https://flask.palletsprojects.com/en/2.2.x/api/#flask.request

        Page.on_url_request

        """
        return request

    def signup_user(self, username, password):
        if self._user_cls is None:
            raise Exception("You have not created the user database yet.")
        if self.username_exists(username):
            return
        new_user = self._user_cls(username=username, password=password)
        self._db.session.add(new_user)
        self._db.session.commit()
        login_user(new_user)

    def signin_user(self, username, password):
        if self._user_cls is None:
            raise Exception("You have not created the user database yet.")
        user = self._user_cls.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)

    def signout_user(self):
        logout_user()

    def username_exists(self, username):
        if self._user_cls is None:
            raise Exception("You have not created the user database yet.")
        if self._user_cls.query.filter_by(username=username).first():
            info("User exists")
            return True
        else:
            return False

    @staticmethod
    def get_current_user():
        return current_user

    def set_restriction(self, username, password):
        """
        Makes the app private.

        Adds a username and password to the app.

        Parameters
        ----------
        username: str

        password: str

        """
        self._auth = BasicAuth(self.flask_app)
        self.flask_app.config['BASIC_AUTH_USERNAME'] = username
        self.flask_app.config['BASIC_AUTH_PASSWORD'] = password

    def set_ws_validation(self, func):
        """
        Validate `simple_websocket.ws.Server` object before sending and accepting data.

        ToUI uses Flask-Sock for websocket communication. Flask-Sock generates a
        `simple_websocket.ws.Server` object when a connection is established. If you
        wanted to access this object before sending and receiving data, input a function
        that has one argument `ws`. This function should either return ``True`` or ``False``.
        If the function returns ``False``, no data will be sent or received using ToUI with
        the client.

        Parameters
        ----------
        func: Callable
            A function that validates the Server object. It should have one argument `ws` and
            should either return ``True`` or ``False``.

        See Also
        --------
        flask_sock
        simple_websockets

        """
        self._validate_ws = func

    def set_data_validation(self, func):
        """
        Validate data received from JavaScript before using it.

        ToUI receives data from JavaScript in the form of a JSON object. To validate this data
        before allowing ToUI to use it, input a function that checks the data. This function
        should have one argument `data` and should either return ``True`` or ``False``.
        If the function returns ``False``, the data will not be used by ToUI.

        You can check the structures of the data received from JavaScript in
        https://toui.readthedocs.io/en/latest/how_it_works.html#instructions-sent-and-received.
        Note that the structures of the JSON objects might change in future versions of ToUI.

        Parameters
        ----------
        func: Callable
            A function that validates data received from JavaScript. It should have one argument
            `data` and should either return ``True`` or ``False``.

        See Also
        --------
        Website.set_ws_validation

        """
        self._validate_data = func

    def register_toui_blueprint(self, blueprint, **options):
        """
        Registers a `ToUIBlueprint` object. It is similar to `Flask.register_blueprint`.

        Parameters
        ----------
        blueprint: toui.structure.ToUIBlueprint

        options
            Same as `Flask.register_blueprint` `options` parameter.

        See Also
        --------
        toui.structure.ToUIBlueprint
        flask.Blueprint

        """
        self.add_pages(*blueprint.pages, blueprint=blueprint)
        self.flask_app.register_blueprint(blueprint=blueprint, **options)


class _DesktopAppApi:

    def __init__(self, app):
        self.app = app

    def communicate(self, data_from_js):
        self.app._communicate(data_from_js, self.window)


class DesktopApp(_App):
    """
    A class that creates a desktop application from HTML files.

    Attributes
    ----------
    name: str
        The name of the app

    pages: list
        A list of added `Page` objects.

    user_vars: dict
        A normal dictionary. It was created only to make the API for the `Website` class and
        `DesktopApp` class similar.

    Examples
    --------

    Creating a desktop app:

    >>> from toui import DesktopApp
    >>> app = DesktopApp("MyApp")

    Creating a page and adding it to the app:

    >>> from toui import Page
    >>> home_page = Page(html_str="<h1>This is the home page</h1>")
    >>> app.add_pages(home_page)

    Running the app:

    >>> if __name__ == "__main__":
    ...     app.run() # doctest: +SKIP

    See Also
    --------
    :py:class:`toui.pages.Page`
    :py:class:`Website`

    """
    def __init__(self, name="App", assets_folder=None):
        """

        Parameters
        ----------
        name: str
            The name of the app.

        """
        self.name = name
        self.pages = []
        if not assets_folder:
            assets_folder = "."
        self._assets_folder = assets_folder
        self._variables = {}
        self._functions = {}
        self._is_running = False

    def add_pages(self, *pages, do_copy=False):
        """
        Adds pages to the app.

        Parameters
        ----------
        pages: list(Page)
            List of `Page` objects.

        do_copy: bool, default = False
            If ``True``, the `Page` will be copied before adding to the app.

        """
        for page in pages:
            if do_copy:
                page = copy(page)
            page._add_script("desktop")
            page._app = self
            self.pages.append(page)
            for func in page._functions.values():
                self._add_functions(func)

    def open_new_page(self, url):
        """
        Opens a new window that has the specified URL.

        This function should only be called after the app starts running.

        Parameters
        ----------
        url: str
            URL of the new page.

        Returns
        -------
        None

        """
        for p in self.pages:
            if p.url == url:
                api = _DesktopAppApi(self)
                p._create_window(name=self.name, api=api, assets_folder=self._assets_folder)

    def get_user_page(self):
        """
        Returns the current `Page`.

        This function should only be called after the app starts running.

        Returns
        -------
        pg: Page

        """
        if not self._is_running:
            raise ToUIWrongPlaceException(f"The function `get_user_page` should only be called after the app runs.")
        func_frame = inspect.currentframe()
        func_type = type(None)
        while func_type is not _FuncWithPage:
            func_frame = func_frame.f_back
            if "self" in func_frame.f_locals:
                func_type = func_frame.f_locals['self'].__class__
            if func_frame is None:
                raise Exception("Could not find page. Perhaps `get_user_page` was not called within a function"
                                "called by HTML event?")
        page = func_frame.f_locals['self'].page
        return page

    @property
    def user_vars(self):
        return self._variables

    def run(self, *args, **kwargs):
        """
        Runs the app. It calls the function `webview.start`. The arguments will be passed to
        `webview.start` function.

        Parameters
        ----------
        args: Any

        kwargs: Any

        """
        if len(self.pages) == 0:
            raise Exception("You need to have at least one `Page` added before running the app.")
        api = _DesktopAppApi(self)
        func = self.pages[0]._create_first_window(name=self.name, api=api, assets_folder=self._assets_folder)
        self._is_running = True
        webview.start(func)

    def _communicate(self, data_from_js, window):
        debug("communicating")
        s = time.time()
        data_dict = json.loads(data_from_js)
        debug(data_dict)
        func = data_dict['func']
        args = data_dict['args']
        new_html = data_dict['html']
        new_page = Page()
        new_page.from_str(new_html)
        new_page._app = self
        new_page._signal_mode = True
        new_page.window = window
        if self._func_exists(func):
            self._call_func(func, *args, page=new_page)
        e = time.time()
        debug(f"TIME: {e - s}s")


def quick_website(name="App", html_file=None, html_str=None, url="/", assets_folder=None, secret_key=None):
    """
    Creates a web app and adds a single `Page` to it.

    Parameters
    ----------
    name: str (optional)
        The name of the app.

    html_file: str (optional)
        The path to the HTML file that will be used to create the `Page`.

    html_str: str (optional)
        The content of the `Page`.

    url: str (optional)
        The URL of the `Page`.

    assets_folder: str (optional)
        The path to the folder that contains the HTML file. If no HTML files are used,
        you can ignore this parameter.

    secret_key: str (optional)
        Sets the `secret_key` attribute for `flask.Flask`

    Returns
    -------
    Website

    """
    app = Website(name=name, assets_folder=assets_folder, secret_key=secret_key)
    page = Page(url=url, html_file=html_file, html_str=html_str)
    app.add_pages(page)
    return app


def quick_desktop_app(name="App", html_file=None, html_str=None, url="/", assets_folder=None):
    """
    Creates a desktop app and adds a single `Page` to it.

    Parameters
    ----------
    name: str (optional)
        The name of the app.

    html_file: str (optional)
        The path to the HTML file that will be used to create the `Page`.

    html_str: str (optional)
        The content of the `Page`.

    url: str (optional)
        The URL of the `Page`.

    assets_folder: str (optional)
        The path to the folder that contains the HTML file. If no HTML files are used,
        you can ignore this parameter.

    Returns
    -------
    DesktopApp

    """
    app = DesktopApp(name=name, assets_folder=assets_folder)
    page = Page(url=url, html_file=html_file, html_str=html_str)
    app.add_pages(page)
    return app

if __name__ == "__main__":
    import doctest
    results = doctest.testmod()
    print(results)