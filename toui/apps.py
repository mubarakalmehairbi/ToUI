"""
A module that creates web apps and desktop apps.
"""
import __main__
import threading
import json
import uuid
import time
import os
from copy import copy
from abc import ABCMeta, abstractmethod
from collections import UserDict
from collections.abc import MutableMapping
from functools import wraps
from typing import Any
from flask import Flask, session, request, send_file, make_response
from flask_sock import Sock
import webview
from toui._helpers import warn, info, debug, error
from toui.pages import Page
from toui.exceptions import ToUIWrongPlaceException, ToUINotAddedError
from toui._defaults import validate_ws, validate_data

_imported_optional_reqs = {'flask-login':False,
                          'flask-sqlalchemy':False,
                          'flask-basicauth':False}

try:
    from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, AnonymousUserMixin
    _imported_optional_reqs['flask-login'] = True
except ModuleNotFoundError: pass

try:
    from flask_sqlalchemy import SQLAlchemy
    _imported_optional_reqs['flask-sqlalchemy'] = True
except ModuleNotFoundError: pass

try:
    from flask_basicauth import BasicAuth
    _imported_optional_reqs['flask-basicauth'] = True
except ModuleNotFoundError: pass


class _ReqsChecker:

    def __init__(self, reqs) -> None:
        self.reqs = reqs

    def __call__(self, func) -> Any:
        @wraps(func)
        def new_func(*args, **kwargs):
            for req in self.reqs:
                if _imported_optional_reqs[req]:
                    return func(*args, **kwargs)
                else:
                    raise ModuleNotFoundError(f"You have not installed the optional package `{req}` yet, to install it run:\n\tpip install {req}")
        return new_func


class _App(metaclass=ABCMeta):
    """The base class for DesktopApp and Website"""

    def __init__(self, name=None, assets_folder=None, secret_key=None, vars_timeout=86400, gen_sid_algo=None):
        """

        Parameters
        ----------
        name: str (optional)
            The name of the app.

        assets_folder: str (optional)
            The path to the folder that contains the HTML files and other assets.

        secret_key: str (optional)
            Sets the `secret_key` attribute for `flask.Flask`. You can also set the environment variable SECRET_KEY from
            the command line and ToUI will get it using `os.environ`.

        vars_timeout: int (optional)
            The timeout interval before the temporary user-specific variables are deleted from `user_vars` attribute.
            The default is 86400 seconds (1 day).

        gen_sid_algo: Callable (optional)
            A callable that generates a unique user id so that ToUI can store data for each user/browser. If ``None``, the
            IP address, user agent, and secret key will be used.

            
        Attributes
        ----------
        flask_app: Flask
            ToUI creates applications using `Flask`. You can access the `Flask` object using the attribute `flask_app`.

        forbidden_urls: list
            These are URLs that ToUI does not allow the user to use because ToUI uses them.

        user_vars: dict
            A dictionary that stores temporary data unique to each user.

        pages: list
            A list of added `Page` objects.


        .. admonition:: Behind The Scenes
            :class: tip
            
            ToUI uses `Flask` and its extenstions to create apps. When creating an instance of this class, the following
            extensions are used:

            - `Sock` class extension from `Flask-Sock` package.

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
        if secret_key is not None:
            self.flask_app.secret_key = secret_key
        elif os.environ.get('SECRET_KEY') is not None:
            self.flask_app.secret_key = os.environ.get('SECRET_KEY')
        else:
            warn("No secret key was set. Generating a random secret key for Flask.")
            self.flask_app.secret_key = os.urandom(50)
        self.pages = []
        self._add_communication_method()
        self._add_user_vars(timeout_interval=vars_timeout, gen_sid_algo=gen_sid_algo)
        self.flask_app.route("/toui-download-<path_id>", methods=['POST', 'GET'])(self._download)
        self.forbidden_urls = ['/toui-communicate', "/toui-download-<path_id>"]
        self._validate_ws = validate_ws
        self._validate_data = validate_data
        self._auth = None
        self._user_cls = None

    @abstractmethod
    def run(self): pass

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
            page._app = self
            page._add_script()
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

    def open_new_page(self, url, new=False):
        """
        Opens another URL.

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
            self.get_user_page()._open_another_page(url, new=new)
        except RuntimeError:
            raise ToUIWrongPlaceException(f"The function `open_new_page` should only be called after the app runs.")

    @staticmethod
    def get_user_page() -> Page:
        """
        A static method that returns the current `Page`.

        This function should only be called after the app starts running.

        Returns
        -------
        pg: Page

        """
        try:
            return session['user page']
        except RuntimeError as e:
            raise ToUIWrongPlaceException(f"The function `get_user_page` should only be called after the app runs.")

    @property
    def user_vars(self):
        """Gets user-specific variables."""
        return self._user_vars

    def download(self, filepath, new=True):
        """
        Downloads a file from the server to a client.
        
        Parameters
        ----------
        filepath: str
            The path to the file (on the server).

        new: bool, default=True
            Opens new tab/window when downloading file.

        """
        path_id = 0
        while self._user_vars._get(f'toui-download-{path_id}'):
            path_id += 1
        self._user_vars._set(f'toui-download-{path_id}', filepath)
        self.open_new_page(f"/toui-download-{path_id}", new=new)

    @_ReqsChecker(['flask-sqlalchemy', 'flask-login'])
    def add_user_database(self, database_uri, other_columns=[], user_cls=None):
        """
        Creates a simple database that has data specific to each user.

        The database is a table that contains the following columns: `username`, `password`, and `id`. To add other columns,
        add their names in `other_columns` list.  Note that this is different from `user_vars` which is a stores temporary
        data without the need to sign in.

        Parameters
        ----------
        database_uri: str
            The URI of the database that you want to connect to.

        other_columns: list
            The names of table columns other than `username`, `password`, and `id`.

        user_cls: Callable, default=None
            If this parameter is ``None``, a table called `User` will be created. However, if this parameter was set, the
            table `User` will not be created and the parameter `user_cls` will be used instead.


        .. admonition:: Behind The Scenes
            :class: tip
            
            The following flask extensions are used when calling this function:

            - `SQLAlchemy` class extension from `Flask-SQLAlchemy` package.
            - `LoginManager` class extension from `Flask-Login` package.

            The following `Flask` configurations are also set:

            - `SQLALCHEMY_DATABASE_URI = database_uri`

        """
        self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        self._db = SQLAlchemy(self.flask_app)
        self._login_manager = LoginManager(self.flask_app)
        self._load_user = self._login_manager.user_loader(self._load_user)
        if not user_cls:
            class User(UserMixin, self._db.Model):
                __tablename__ = "user"

                id = self._db.Column(self._db.Integer, primary_key=True)
                username = self._db.Column(self._db.String, nullable=False, unique=True)
                password = self._db.Column(self._db.String, nullable=False, unique=False)

                def __repr__(self):
                    return f'<User {self.username}>'
            for col in other_columns:
                setattr(User, col, self._db.Column(self._db.String))
        else:
            User = user_cls
        self._user_cls = User
        with self.flask_app.app_context():
            self._db.create_all()

    # Website-specific methods
    @staticmethod
    def get_request():
        """
        A static method that gets data sent from client using HTTP request.

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

    @_ReqsChecker(['flask-sqlalchemy', 'flask-login'])
    def signup_user(self, username, password, **other_info):
        """
        Creates a new user in the database.
        
        Parameters
        ----------
        username: str

        password: str

        other_info
            Other information required for signing up.

        Returns
        -------
        bool
            ``True`` if the user is created, and ``False`` if it is not created.

        """
        self._confirm_user_database_created()
        if self.username_exists(username):
            return False
        new_user = self._user_cls(username=username, password=password, **other_info)
        self._db.session.add(new_user)
        self._db.session.commit()
        if self.username_exists(username):
            return True
        else:
            return False

    @_ReqsChecker(['flask-sqlalchemy', 'flask-login'])
    def signin_user(self, username, password, **other_info):
        """
        Loads the data of a user from database.

        Parameters
        ----------
        username: str

        password: str

        other_info
            Other information required for signing in.

        Returns
        -------
        bool
            ``True`` if the user is signed in, and ``False`` if it is not signed in.

        """
        self._confirm_user_database_created()
        user = self._user_cls.query.filter_by(username=username, password=password, **other_info).first()
        if user:
            login_user(user)
            self._user_vars._set("user-id", user.id)
            return True
        else:
            return False
        
    @_ReqsChecker(['flask-sqlalchemy', 'flask-login'])
    def signin_user_from_id(self, user_id, **other_info):
        """
        Loads the data of a user from database using the user's ID.

        Parameters
        ----------
        id: int

        other_info
            Other information required for signing in.

        Returns
        -------
        bool
            ``True`` if the user is signed in, and ``False`` if it is not signed in.

        """
        self._confirm_user_database_created()
        user = self._user_cls.query.filter_by(id=user_id, **other_info).first()
        if user:
            login_user(user)
            self._user_vars._set("user-id", user_id)
            return True
        else:
            return False

    @_ReqsChecker(['flask-login'])
    def signout_user(self):
        """
        A method that signs out the current user.
        """
        logout_user()
        self._user_vars._del('user-id')

    @_ReqsChecker(['flask-sqlalchemy'])
    def username_exists(self, username):
        """
        Checks if the username is exists in the database.
        
        Parameters
        ----------
        username: str
        
        Returns
        -------
        bool
            ``True`` if the username exists, otherwise ``False``.
            """
        self._confirm_user_database_created()
        if self._user_cls.query.filter_by(username=username).first():
            info(f"User {username} exists")
            return True
        else:
            return False

    @staticmethod
    @_ReqsChecker(['flask-login'])
    def get_current_user():
        """
        A static method that returns the current user.
        """
        if isinstance(current_user, AnonymousUserMixin):
            return None
        else:
            return current_user

    @_ReqsChecker(['flask-basicauth'])
    def add_restriction(self, username, password):
        """
        Makes the app private.

        Adds a username and password to the app.

        Parameters
        ----------
        username: str

        password: str


        .. admonition:: Behind The Scenes
            :class: tip
            
            When calling this method, the following `Flask` extension is used:

            - `BasicAuth` class extension from `Flask-BasicAuth` package.

            The following `Flask` configurations are also set:

            - `BASIC_AUTH_USERNAME = username`
            - `BASIC_AUTH_PASSWORD = password`

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
        set_ws_validation

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

    def _add_communication_method(self):
        self.flask_app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
        self._socket = Sock(self.flask_app)
        self._socket.route("/toui-communicate")(self._communicate)

    def _add_user_vars(self, timeout_interval, gen_sid_algo):
        self._user_vars = _UserVars(self, timeout_interval=timeout_interval, gen_sid_algo=gen_sid_algo)

    def _session_check(self):
        """This is a private function."""
        try:
            session.keys()
        except RuntimeError as e:
            return False
        if not "user page" in session.keys():
            session['user page'] = None
        if not "_user_id" in session.keys():
            user_id = self._user_vars._get('user-id')
            if user_id:
                session['_user_id'] = user_id
        return True
    
    def _download(self, path_id):
        debug(f"PATH: {path_id}")
        file_to_download = self._user_vars._get(f'toui-download-{path_id}')
        debug(f"File to download: {file_to_download}")
        if file_to_download:
            return send_file(file_to_download, as_attachment=True)

    def _communicate(self, ws):
        """This is a private function."""
        validation = self._validate_ws(ws)
        if not validation:
            info("WebSocket validation returns `False`. No data should be sent or received.")
            return
        info(f'WebSocket connected: {ws.connected}')
        ws.msg_num = 0
        ws.pending_messages = {}
        ws.pending_pages = []
        while True:
            valid_message = False
            while not valid_message:
                data_from_js = ws.receive()
                data_validation = self._validate_data(data_from_js)
                if not data_validation:
                    info("Data validation returns `False`. The data will not be used.")
                    continue
                s = time.time()
                data_dict = json.loads(data_from_js)
                if data_dict.get("type") == "page":
                    ws.pending_pages.append(data_dict)
                    valid_message = True
            while True:
                debug(f"Pages Before: {len(ws.pending_pages)}")
                if len(ws.pending_pages) == 0:
                    break
                data_dict = ws.pending_pages.pop(0)
                debug(f"Pages After: {len(ws.pending_pages)}")
                self._session_check()
                func = data_dict['func']
                args = data_dict['args']
                url = data_dict['url']
                new_html = data_dict['html']
                new_page = Page(url=url)
                new_page.from_str(new_html)
                new_page._app = self
                new_page._signal_mode = True
                new_page._ws = ws
                new_page._inherit_functions()
                selector_to_element = data_dict['selector-to-element']
                if selector_to_element:
                    for index, arg in enumerate(args):
                        if type(arg) is dict:
                            if arg.get('type') == "element":
                                args[index] = new_page.get_element_from_selector(arg['selector'])
                if "uid" in data_dict:
                    new_page._uid = data_dict['uid']
                session['user page'] = new_page
                try:
                    if new_page._func_exists(func):
                        new_page._call_func(func, *args)
                    del session['user page']
                except Exception as e:
                    del session['user page']
                    raise e
                e = time.time()
                debug(f"TIME: {e - s}s")

    def _confirm_user_database_created(self):
        if self._user_cls is None:
            raise ToUINotAddedError("You have not created the user database yet. To create it, call the method: `add_user_database`.")

    def _load_user(self, user_id):
        return self._user_cls.query.filter_by(id=int(user_id)).first()


class _FuncWithPage:
    """Currently this class is unused, but it might be used later."""
    def __init__(self, func, page):
        self.func = func
        self.page = page
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class _UserVars(MutableMapping):
    """User-specific variables"""

    def __init__(self, app, timeout_interval, gen_sid_algo) -> None:
        self._app = app
        self._cache = UserDict()
        self._cache.set = self._cache.__setitem__
        self._default_vars = {}
        self._timeout_interval = timeout_interval
        if gen_sid_algo:
            self._gen_sid = gen_sid_algo

    def _gen_sid(self):
        try:
            if request.cookies.get('TOUI_SID'):
                sid = request.cookies.get('TOUI_SID')
                session['toui-sid'] = sid
            else:
                if "toui-sid" in session:
                    sid = session['toui-sid']
                else:
                    sid = str(uuid.uuid4())
                    session['toui-sid'] = sid
                response = make_response()
                response.set_cookie("TOUI_SID", sid, secure=True, httponly=True)
                session['toui-response'] = response
            return sid
        except RuntimeError:
            return None
        
    def _timeout(self, sid):
        self._cache.delete(sid)

    def _sid_check(self):
        sid = self._gen_sid()
        if sid:
            user_dict = self._cache.get(sid)
            if user_dict is None:
                self._cache.set(sid, {"toui-vars": self._default_vars.copy()})
                threading.Timer(self._timeout_interval, self._timeout, args=[sid]).start()
            return sid

    def _get_toui_vars(self):
        sid = self._sid_check()
        if sid:
            return self._cache.get(sid)['toui-vars']
        else:
            return self._default_vars

    def _get(self, key):
        sid = self._sid_check()
        if sid:
            return self._cache.get(sid).get(key)
        else:
            return self._default_vars
    
    def _set(self, key, value):
        """Avoid key='toui-vars'"""
        sid = self._sid_check()
        if sid:
            sid_dict = self._cache.get(sid)
            sid_dict[key] = value
        else:
            self._default_vars[key] = value

    def _del(self, key):
        sid = self._sid_check()
        if sid:
            sid_dict = self._cache.get(sid)
            del sid_dict[key]
        else:
            del self._default_vars[key]

    def __getitem__(self, key):
        return self._get_toui_vars()[key]
    
    def __setitem__(self, key, value):
        toui_vars = self._get_toui_vars()
        toui_vars[key] = value

    def __delitem__(self, key: Any) -> None:
        toui_vars = self._get_toui_vars()
        del toui_vars[key]

    def __iter__(self):
        for key in self._get_toui_vars():
            yield key

    def __len__(self) -> int:
        return len(self._get_toui_vars())
    
    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_toui_vars(), name)
    
    def __repr__(self) -> str:
        return repr(self._get_toui_vars())
    

class Website(_App):
    """
    A class that creates a web application from HTML files.

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

    @wraps(Flask.run)
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


class DesktopApp(_App):
    """
    A class that creates a desktop application from HTML files.


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
    def _run_server(self):
        self.flask_app.run(port=self._port, use_reloader=False)

    @wraps(webview.start)
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
            raise Exception("Cannot run the app because no pages were added.")
        self._port = webview.http._get_random_port()
        t = threading.Thread(target=self._run_server)
        t.daemon = True
        t.start()
        self.pages[0]._create_window()
        webview.start(*args, **kwargs)


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


def quick_desktop_app(name="App", html_file=None, html_str=None, url="/", assets_folder=None, secret_key=None):
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
    app = DesktopApp(name=name, assets_folder=assets_folder, secret_key=secret_key)
    page = Page(url=url, html_file=html_file, html_str=html_str)
    app.add_pages(page)
    return app


def set_global_app(app):
    """
    Allows the app object to be shared across Python modules.

    Examples
    --------

    Suppose you have two Python scripts, "main.py" and "home_page.py". In "main.py", you can create the app
    and make it global:

    >>> from toui import Website, set_global_app
    >>> app = Website(__name__)
    >>> set_global_app(app)

    While in "home_page.py", you can get the shared app:

    >>> from toui import get_global_app
    >>> app = get_global_app()

    """
    global _global_app
    _global_app = app


def get_global_app() -> _App:
    """
    Gets the shared app object.

    See :py:meth:`set_global_app`.
    """
    return _global_app


if __name__ == "__main__":
    import doctest
    results = doctest.testmod()
    print(results)