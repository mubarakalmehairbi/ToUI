![ToUI Image](https://github.com/mubarakalmehairbi/ToUI/blob/main/images/logo.png?raw=True)

![License](https://img.shields.io/github/license/mubarakalmehairbi/ToUI)
![PyPI - Downloads](https://img.shields.io/pypi/dm/toui)
![Latest version](https://img.shields.io/pypi/v/toui)
![Docs](https://img.shields.io/readthedocs/toui)

# Overview
ToUI is a Python framework for creating user interfaces (websites and desktop apps)
from HTML (and CSS) code easily. It allows you to call your Python functions from HTML. No JavaScript knowledge is required, but some knowledge of HTML
is usually required.

# Why ToUI
- Converts HTML and CSS files into a fast-responsive app using Python alone.
- Simple to understand for programmers who only know Python and HTML.
- The method of creating websites and the method of creating desktop apps are similar, which makes it easy to convert a website to a desktop app and vice versa.

# How to install
Run this command:
```shell
pip install toui
```

# How to create a basic website
Import the required classes:
```python
from toui import Website, Page
```
Create a `Website` object:
```python
app = Website(name=__name__, assets_folder="path/to/assets_folder",  secret_key="some secret key")
```
Create a `Page` and add it to the website:
```python
main_page = Page(html_file="path/to/html", url="/")
app.add_pages(main_page)
```
Run the app:
```python
if __name__ == "__main__":
    app.run()
```
The complete code:
```python
from toui import Website, Page

app = Website(name=__name__, assets_folder="path/to/assets_folder", 
              secret_key="some secret key")

main_page = Page(html_file="path/to/html", url="/")
app.add_pages(main_page)

if __name__ == "__main__":
    app.run()
```

# How to create a desktop app
Creating a desktop app is similar to creating a website. Only replace `Website` class with
`DesktopApp`:
```python
from toui import DesktopApp, Page

app = DesktopApp(name="MyApp", assets_folder="path/to/assets_folder")

main_page = Page(html_file="path/to/html", url="/")
app.add_pages(main_page)

if __name__ == "__main__":
    app.run()
```

# Make the app responsive
Check this [example](https://toui.readthedocs.io/en/latest/Examples.example_1_simple_website.html)
and [other examples](https://toui.readthedocs.io/en/latest/Examples.html) to learn how
to make the website / desktop app responsive.

# Deploy the app
You can deploy the web app the same way you deploy a `Flask` app ([How to deploy Flask app](https://flask.palletsprojects.com/deploying/)).
The only difference is that you need to access the `Flask` object first:
```python
app = Website(__name__)
flask_app = app.flask_app
```
Then you need to deploy the `flask_app` and not the `app`.

# How to contribute
ToUI welcomes contribution, small or big. For anyone who wants to contribute please check the [contribution page](https://toui.readthedocs.io/en/latest/CONTRIBUTING.html).

# License and Copyrights
Copyrights (c) 2023 Mubarak Almehairbi.
This package is licensed under the MIT license.

# Documentation
You can find the documentation in this link: [ToUI docs](https://toui.readthedocs.io).
