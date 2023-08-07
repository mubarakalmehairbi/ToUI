"""
A module that creates web apps and desktop apps.
"""
import __main__
import threading
import json
import uuid
import time
import os
import requests
from copy import copy
from abc import ABCMeta, abstractmethod
from collections import UserDict
from collections.abc import MutableMapping
from functools import wraps
from typing import Any, Union
from flask import Flask, session, request, send_file, make_response, redirect
from flask_sock import Sock
import webview
from toui._helpers import warn, info, debug, error
from toui.pages import Page
from toui.exceptions import ToUIWrongPlaceException, ToUINotAddedError, ToUIOverlapException
from toui._defaults import validate_ws, validate_data

_imported_optional_reqs = {'flask-login':False,
                          'flask-sqlalchemy':False,
                          'flask-basicauth':False,
                          'firebase_admin': False}

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

try:
    import firebase_admin
    import firebase_admin.db
    import firebase_admin.firestore
    import firebase_admin.credentials
    import firebase_admin.storage
    import firebase_admin.auth
    _imported_optional_reqs['firebase_admin'] = True
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
        self.flask_app.route("/toui-google-sign-in", methods=['POST', 'GET'])(self._sign_in_using_google)
        self.forbidden_urls = ['/toui-communicate', "/toui-download-<path_id>", "/toui-google-sign-in"]
        self._validate_ws = validate_ws
        self._validate_data = validate_data
        self._auth = None
        self._user_cls = None
        self._user_db_type = None
        self._firebase_app = None
        self._firebase_db = None
        self._google_data = {}

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

    @_ReqsChecker(['firebase_admin'])
    def add_firebase(self, firebase_config: Union[dict, str], **options):
        """
        Adds Firebase to the app.

        Parameters
        ----------
        firebase_config: dict, str
            The Firebase configuration dictionary or the path of credentials JSON.

        options (optional)
            Extra options for initializing Firebase. See `Google's documentation <https://firebase.google.com/docs/reference/admin/python/firebase_admin#initialize_app>`_.
        """
        certificate = firebase_admin.credentials.Certificate(firebase_config)
        self._firebase_app = firebase_admin.initialize_app(certificate, options)

    def store_file_using_firebase(self, destination_path, file_path, bucket_name=None):
        """
        Uploads a file to Firebase storage.

        Parameters
        ----------
        destination_path: str
            The path of the file in Firebase storage.

        file_path: str
            The path of the file on the server.

        bucket_name: str, default = None
            The name of the bucket. If ``None``, the default bucket will be used. However, if you did not specify "storageBucket"
            option in the Firebase configuration, you must specify the bucket name in this function.

        Returns
        -------
        None

        """
        bucket = firebase_admin.storage.bucket(name=bucket_name)
        blob = bucket.blob(destination_path)
        blob.upload_from_filename(file_path)

    def get_file_from_firebase(self, source_path, new_file_path, bucket_name=None):
        """
        Downloads a file from Firebase storage.

        Parameters
        ----------
        source_path: str
            The path of the file in Firebase storage.

        new_file_path: str
            The path of the file on the server.

        bucket_name: str, default = None
            The name of the bucket. If ``None``, the default bucket will be used. However, if you did not specify "storageBucket"
            option in the Firebase configuration, you must specify the bucket name in this function.

        Returns
        -------
        None

        """
        bucket = firebase_admin.storage.bucket(name=bucket_name)
        blob = bucket.blob(source_path)
        blob.download_to_filename(new_file_path)

    @_ReqsChecker(['flask-sqlalchemy', 'flask-login'])
    def add_user_database_using_sql(self, database_uri, other_columns=[], user_cls=None):
        """
        Creates a simple database that has data specific to each user.

        The database has a table that contains the following columns: `username`, `password`, and `id`. To add other columns,
        add their names in `other_columns` list.  Note that this is different from `user_vars` which is a stores temporary
        data without the need to sign in.

        Warning
        -------
        A table called `users` will be created in the database. If you already have a table with the same name, it might be
        overwritten.

        Parameters
        ----------
        database_uri: str
            The URI of the database that you want to connect to.

        other_columns: list
            The names of table columns other than `username`, `password`, `email` and `id`.

        user_cls: Callable, default=None
            If this parameter is ``None``, a table called `users` will be created. However, if this parameter was set, the
            table `users` will not be created and the parameter `user_cls` will be used instead.


        .. admonition:: Behind The Scenes
            :class: tip
            
            The following flask extensions are used when calling this function:

            - `SQLAlchemy` class extension from `Flask-SQLAlchemy` package.
            - `LoginManager` class extension from `Flask-Login` package.

            The following `Flask` configurations are also set:

            - `SQLALCHEMY_DATABASE_URI = database_uri`

        """
        if self._user_db_type == "firebase":
            raise ToUIOverlapException("This function cannot be called when using Firebase user database.")
        self._user_db_type = "sql"
        self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        self._db = SQLAlchemy(self.flask_app)
        self._login_manager = LoginManager(self.flask_app)
        self._load_user = self._login_manager.user_loader(self._load_user)
        if not user_cls:
            class User(UserMixin, self._db.Model):
                __tablename__ = "users"

                id = self._db.Column(self._db.Integer, primary_key=True)
                username = self._db.Column(self._db.String, nullable=False, unique=True)
                email = self._db.Column(self._db.String, nullable=True, unique=True)
                password = self._db.Column(self._db.String, nullable=True, unique=False)

                def __repr__(self):
                    return f'<User {self.username}>'
            for col in other_columns:
                setattr(User, col, self._db.Column(self._db.String))
        else:
            User = user_cls
        self._user_cls = User
        with self.flask_app.app_context():
            self._db.create_all()

    @_ReqsChecker(['firebase_admin'])
    def add_user_database_using_firebase(self):
        """
        Adds Firebase user database to the app.

        Make sure you create a firestore database (not realtime) in your Firebase app.

        Warning
        -------
        A collection called `users` will be created in the database. If you already have a collection with the same name, it might be overwritten.

        
        .. admonition:: Behind The Scenes
            :class: tip
            
            Firebase authentication and database are used when calling this function.
            
        """
        if self._firebase_app is None:
            raise ToUINotAddedError("Firebase is not added to the app. Use `add_firebase` to add it.")
        if self._user_db_type == "sql":
            raise ToUIOverlapException("This function cannot be called when using SQL user database.")
        self._user_db_type = "firebase"
        self._firebase_db = firebase_admin.firestore.client().collection("users")

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
    
    def redirect_response(self, url):
        """
        Use it with `Page.on_url_request` to redirect the user to another page.

        `Page.on_url_request` is called when the user makes an HTTP request to the page. If you want to redirect the user
        to another page, define a function then use this method as the return value of a function. Then add the function to
        `Page.on_url_request` and set `display_return_value` as ``True``.

        Examples
        --------
        
        >>> def redirect_function():
        ...     return app.redirect_response("/another-page-url")
        >>> home_page.on_url_request(redirect_function, display_return_value=True)

        Parameters
        ----------
        url: str
            The URL of the page that the user will be redirected to.

        """
        return redirect(url)

    def signup_user(self, username, password=None, email=None, **other_info):
        """
        Creates a new user in the database.
        
        Parameters
        ----------
        username: str

        password: str

        email: str

        other_info
            Other information required for signing up.

        Returns
        -------
        bool
            ``True`` if the user is created, and ``False`` if it is not created.

        """
        self._confirm_user_database_created()
        if self.username_exists(username) or self.email_exists(email):
            return False
        if self._user_db_type == "sql":
            new_user = self._user_cls(username=username, password=password, email=email, **other_info)
            self._db.session.add(new_user)
            self._db.session.commit()
        elif self._user_db_type == "firebase":
            if password is not None:
                if len(password) < 6:
                    error("Password for Firebase authentication needs to be at least 6 characters")
                    return False
            user_record = firebase_admin.auth.create_user(password=password, display_name=username, email=email)
            self._firebase_db.document(user_record.uid).set({"username": username, 'password': password,
                                                                         'email': email, **other_info})
        if self.username_exists(username) or self.email_exists(email):
            return True
        else:
            return False

    def signin_user(self, username, password=None, email=None, **other_info):
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
        if not self.username_exists(username) and not self.email_exists(email):
            return False
        if self._user_db_type == "sql":
            filter = {"username": username, **other_info}
            if email is not None:
                filter["email"] = email
            if password is not None:
                filter["password"] = password
            user = self._user_cls.query.filter_by(**filter).first()
            if user:
                login_user(user)
                self._user_vars._set("user-id", user.id)
                return True
            else:
                return False
        elif self._user_db_type == "firebase":
            users = self._firebase_db.where("username", "==", username).get()
            if email is not None:
                users = users[0].where("email", "==", email).get()
                if len(users) == 0:
                    return False
            if password is not None:
                users = users[0].where("password", "==", password).get()
                if len(users) == 0:
                    return False
            return self.signin_user_from_id(users[0].id, **other_info)
        
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
        if self._user_db_type == "sql":
            user = self._user_cls.query.filter_by(id=user_id, **other_info).first()
            if user:
                login_user(user)
                self._user_vars._set("user-id", user_id)
                return True
            else:
                return False
        elif self._user_db_type == "firebase":
            user = firebase_admin.auth.get_user(user_id)

            if user:
                user_dict = user.to_dict()
                for key, value in other_info.items():
                    if user_dict.get(key) != value:
                        return False
                self._user_vars._set("user-id", user_id)
                return True
            else:
                return False
            
    def get_current_user_data(self, key):
        """
        Gets data specific to the currently signed in user from the database.

        Parameters
        ----------
        key: str
            The key (name) of the data. For example: "username", "email", "age", etc.

        Returns
        -------
        Any
            The value of the data.
        """
        self._confirm_user_database_created()
        if not self.is_signed_in():
            error("No user is signed in.")
            return None
        if self._user_db_type == "sql":
            if not key in current_user.__table__.columns:
                error(f"'{key}' was not added as a column in users table")
                return None
            return getattr(current_user, key)
        elif self._user_db_type == "firebase":
            return self._firebase_db.document(self._user_vars._get("user-id")).get().to_dict().get(key)

    def set_current_user_data(self, key, value):
        """
        Sets data specific to the currently signed in user in the database.

        Warning
        -------
        Currently, if you are using SQL database, you can only set data that
        was already added as a column in the users table.


        Parameters
        ----------
        key: str
            The key (name) of the data. For example: "username", "email", "age", etc.

        value: Any
            The value of the data.

        Returns
        -------
        bool
            ``True`` if the data is set, and ``False`` if it is not set.

        """
        self._confirm_user_database_created()
        if not self.is_signed_in():
            error("No user is signed in.")
            return False
        if self._user_db_type == "sql":
            if not key in current_user.__table__.columns:
                error(f"'{key}' was not added as a column in users table")
                return False
            setattr(current_user, key, value)
            self._db.session.commit()
            return True
        elif self._user_db_type == "firebase":
            self._firebase_db.document(self._user_vars._get("user-id")).update({key: value})
            return True
        
    def get_current_user_id(self):
        """
        Gets the ID of the currently signed in user.

        Returns
        -------
        str
            The ID of the user.
        """
        self._confirm_user_database_created()
        if not self.is_signed_in():
            error("No user is signed in.")
            return None
        return self._user_vars._get("user-id")

    def signout_user(self):
        """
        A method that signs out the current user.
        """
        self._confirm_user_database_created()
        if self._user_db_type == "sql":
            logout_user()
        self._user_vars._del('user-id')

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
        if self._user_db_type == "sql":
            if self._user_cls.query.filter_by(username=username).first():
                info(f"User {username} exists")
                return True
            else:
                return False
        elif self._user_db_type == "firebase":
            if len(self._firebase_db.where("username", "==", username).get()) > 0:
                info(f"User {username} exists")
                return True
            else:
                return False
            
    def email_exists(self, email):
        """
        Checks if the email is exists in the database.
        
        Parameters
        ----------
        email: str
        
        Returns
        -------
        bool
            ``True`` if the email exists, otherwise ``False``.
        """
        self._confirm_user_database_created()
        if email is None:
            return False
        if self._user_db_type == "sql":
            if self._user_cls.query.filter_by(email=email).first():
                info(f"Email {email} exists")
                return True
            else:
                return False
        elif self._user_db_type == "firebase":
            if len(self._firebase_db.where("email", "==", email).get()) > 0:
                return True
            else:
                return False

    def is_signed_in(self):
        """
        Checks if the user is signed in.

        Returns
        -------
        bool
        """
        self._confirm_user_database_created()
        if self.user_vars._get('user-id'):
            if self._user_db_type == "sql":
                login_user(self._user_cls.query.filter_by(id=self._user_vars._get("user-id")).first())
            return True
        else:
            return False
        
    def sign_in_using_google(self, client_id, client_secret, after_auth_url, additional_scopes=None, custom_username=None, custom_host=None,
                             **other_params):
        """
        Signs in a user using Google (Experimental).

        Make sure to create a Google app first. Also, add the following as an authorized redirect URI to your Google app:
        ``https://<your-domain>/toui-google-sign-in``
        
        Parameters
        ----------
        client_id: str
            The client ID of the Google app.

        client_secret: str
            The client secret of the Google app.

        after_auth_url: str
            The URL to redirect to after completing authentication. This is not the same as the redirect uri of the Google app, so
            you do not need to register it as an authorized redirect URI in your Google app.

        additional_scopes: list, default=None (optional)
            By default, the user allows the app to only access non-sensitive information such as the user's name and email. If you
            want to access more information, you can pass a list of scopes. For more information, see `Google's documentation <https://developers.google.com/identity/protocols/oauth2/scopes>`_.

        custom_username: str, default=None (optional)
            If you want to use a custom username instead of the user's email, you can pass it here.

        custom_host: str, default=None (optional)
            Only use this option if you need to change the scheme and host of the redirect uri. For example,
            if you want to use ``http://127.0.0.1:5000`` instead of ``http://localhost:5000``, you can pass
            ``http://127.0.0.1:5000`` here.

        other_params: kwargs (optional)
            Keyword arguments that can be passed as parameters to authorization url.For more information, see
            `Google's documentation <https://developers.google.com/identity/protocols/oauth2/web-server#httprest_1>`_.
        """

        self._google_data = {"client_id": client_id, "client_secret": client_secret}
        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
        if additional_scopes:
            for s in additional_scopes:
                scope += f" {s}"
        url = f"/toui-google-sign-in?scope={scope}"
        if custom_username:
            url += f"&username={custom_username}"
        self.user_vars._set('google-redirect-uri-host', custom_host)
        for key, value in other_params.items():
            url += f"&{key}={value}"
        self.user_vars._set('google-after-auth-url', after_auth_url)
        self.open_new_page(url=url)

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
        Validates a WebSocket connection before sending and accepting data.

        ToUI uses Flask-Sock for websocket communication. Flask-Sock generates a
        `simple_websocket.ws.Server <https://simple-websocket.readthedocs.io/en/latest/api.html#the-server-class>`_
        object when a connection is established. If you wanted to access this object before
        sending and receiving data, input a function that has one argument `ws`. This function
        should either return ``True`` or ``False``. If the function returns ``False``, no data
        will be sent or received using ToUI with the client.

        The `ws` argument is a `simple_websocket.ws.Server` object which you can learn about in its
        `documentation <https://simple-websocket.readthedocs.io/en/latest/api.html#the-server-class>`_.
        You might need to do some testing in order to explore the types of data that you can find in
        this object.

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
        Validates data received from JavaScript before using it.

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
        file_to_download = self._user_vars._get(f'toui-download-{path_id}')
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
                if len(ws.pending_pages) == 0:
                    break
                data_dict = ws.pending_pages.pop(0)
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
        if self._user_db_type is None:
            raise ToUINotAddedError("You have not created the user database yet. To create it, call the method: `add_user_database_using_sql` or `add_user_database_using_firebase`.")

    def _load_user(self, user_id):
        return self._user_cls.query.filter_by(id=int(user_id)).first()
    
    def _get_user_details_from_google_token(self, access_token, refresh_token=None):
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:
            if refresh_token:
                r = requests.post("https://oauth2.googleapis.com/token", data={
                    "client_id": self._google_data['client_id'],
                    "client_secret": self._google_data['client_secret'],
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"})
                if r.status_code == 200:
                    return self._get_user_details_from_google_token(r.json()['access_token'])
        raise Exception(f"Error getting user details from Google. Status code: {r.status_code}. Response: {r.text}")
    
    def _sign_in_using_google(self):
        client_id = self._google_data['client_id']
        client_secret = self._google_data['client_secret']
        scope = request.args.get("scope")
        if self.user_vars._get('google-redirect-uri-host') is not None:
            redirect_uri = self.user_vars._get('google-redirect-uri-host') + "/toui-google-sign-in"
        else:
            redirect_uri = request.base_url
        response_type = "code"
        access_type = request.args.get("access_type")
        state = request.args.get("state")
        include_granted_scopes = request.args.get("include_granted_scopes")
        enable_granular_consent = request.args.get("enable_granular_consent")
        login_hint = request.args.get("login_hint")
        prompt = request.args.get("prompt")
        after_auth_url = self.user_vars._get('google-after-auth-url')
        username = request.args.get("username")
        if "code" in request.args:
            code = request.args.get("code")
            self.user_vars._set('google-redirect-uri-host', None)
            dictToSend = {'code':code,
                          'client_id':client_id,
                          'client_secret':client_secret,
                          'grant_type':'authorization_code',
                          'redirect_uri':redirect_uri}
            res = requests.post('https://oauth2.googleapis.com/token', data=dictToSend,
                                headers={'Host': 'oauth2.googleapis.com',
                                         'Content-Type':'application/x-www-form-urlencoded'})
            dictFromServer = res.json()
            info(f"Google response keys: {dictFromServer.keys()}")
            self.user_vars._set('google-access-token', dictFromServer['access_token'])
            if 'refresh_token' in dictFromServer:
                self.user_vars._set('google-refresh-token', dictFromServer['refresh_token'])
            user_details = self._get_user_details_from_google_token(access_token=dictFromServer['access_token'], refresh_token=self.user_vars._get('google-refresh-token'))
            self.user_vars._set('google-user-details', user_details)
            email = user_details['email']
            if username is None:
                username = email
            if self.email_exists(email):
                self.signin_user(email=email, username=username, password=None)
            else:
                success = self.signup_user(email=email, username=username, password=None)
                if success:
                    self.signin_user(email=email, username=username, password=None)
                else:
                    error("Error signing up user")
            return redirect(after_auth_url)
        else:
            # Validating scope
            for s in scope.split(" "):
                if not s.startswith("https://www.googleapis.com/auth/"):
                    raise ValueError(f"Invalid scope. Scope should start with `https://www.googleapis.com/auth/`. However your scope is `{s}`")
            
            # Creating redirect_to
            redirect_to = f"https://accounts.google.com/o/oauth2/v2/auth?" \
                      f"client_id={client_id}" \
                      f"&response_type={response_type}" \
                      f"&scope={scope}" \
                      f"&redirect_uri={redirect_uri}"
            
            if access_type is not None:
                redirect_to += f"&access_type={access_type}"
            if state is not None:
                redirect_to += f"&state={state}"
            if include_granted_scopes is not None:
                if include_granted_scopes is True:
                    redirect_to += f"&include_granted_scopes=true"
                elif include_granted_scopes is False:
                    redirect_to += f"&include_granted_scopes=false"
            if enable_granular_consent is not None:
                if enable_granular_consent is True:
                    redirect_to += f"&enable_granular_consent=true"
                elif enable_granular_consent is False:
                    redirect_to += f"&enable_granular_consent=false"
            if login_hint is not None:
                redirect_to += f"&login_hint={login_hint}"
            if prompt is not None:
                redirect_to += f"&prompt={' '.join(prompt)}"
            return redirect(redirect_to)


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
            if key in sid_dict:
                del sid_dict[key]
        else:
            if key in self._default_vars:
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