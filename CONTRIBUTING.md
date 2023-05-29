# Contributing

This instructions below are guidelines for anyone who wants to contribute to ToUI. You need do not need to be an expert in ToUI in order to contribute to it. Some [areas where you can contribute](#areas-where-you-can-contribute) are simpler than others.

### Contents
- [Structure of the package](#structure-of-the-package)
- [Areas where you can contribute](#areas-where-you-can-contribute)
- [Contributing steps](#contributing-steps)

## Structure of the package
In ToUI there are several modules. The most important modules of ToUI are listed below:

### `apps.py`
This module contains the classes that create applications: `Website` and `DesktopApp`. The base class for these two classes is `_App`. The most important points to understand about `_App` are the following:
- It has the attribute `flask_app` which is an instance of `Flask`.
- It adds new web pages or windows using `add_pages()` methods.
- The private method `_communicate()` is the method that allows the app to receive messages from JavaScript via WebSockets.
- `run()` is an abstract method, which means that any class that inherit `_App` should define a `run()` method.

### `pages.py`
This module allows you to create web pages or windows using HTML. You can create a `Page` object to create a web page or window, then add the page to the app using `Website.add_pages()` or `DesktopApp.add_pages()` methods. In the same module, there is a class called `_PageSignal` which sends instructions related to the page to JavaScript. More information about `_PageSignal` will be explained below ([`_signals.py`](#_signals-py)).

### `elements.py`
This module contains the class `Element`  which allows you to create HTML elements. It also contains the class `_ElementSignal` which sends instructions related to the element to JavaScript. More information about `_ElementSignal` will be explained below ([`_signals.py`](#_signals-py)).

### `_javascript_templates.py`
This module contains a JavaScript code that will be added to each HTML file. The most important notes about this JavaScript code are:
- It connects to the apps `Website` and `DesktopApp` using the `WebSocket` object.
- The JavaScript function `_toPy()` sends the HTML document along with other information to Python using `socket.send()`. The Python method `Website._communicate()` or `DesktopApp._communicate()` receives these information from JavaScript.
- Python sends instructions to JavaScript (more about it below in [`_signals.py`](#_signals-py)). The JavaScript function `_findAndExecute()` executes the instructions sent from Python.

### `_signals.py`
This module allows Python to send instructions to JavaScript. The class `_Signal` is used each time you want to send a signal (instruction) to JavaScript. However, this class is not used directly. You need to use its children classes: `_PageSignal` to send signals related to updating an HTML page, or `_ElementSignal` to send signals related to updating an HTML element. These two classes should decorate the methods that will send the signals. For example, if you check the method `Element.set_attr()` in `elements.py`, you will notice the decorator `_ElementSignal()` above it, which means that if the function `Element.set_attr()` was called after the app starts running, a signal will be sent to JavaScript.

## Areas where you can contribute
### **Mobile apps**
In `apps.py` there are two classes: `Website` which creates websites and `DesktopApp` which creates desktop apps. Mobile apps are not yet included. To include a mobile app, you need to create a new class in `apps.py` that inherits `_App` base class. You also need to define the method `run()` otherwise your new class will not work. Note that the mobile app needs to be based on flask.
  
### **Additional methods for Page class and Element class**
Sometimes you can find some JavaScript functions that update HTML documents or HTML elements that are not yet available in ToUI. If you want to create a new Python method that updates HTML documents or elements, you need to follow the following steps (the steps below are for `Element` class but the same can be applied for `Page` class):
1. Make sure to understand the [structure of ToUI](#structure-of-the-package), especially [`_signals.py`](#signals-py).
2. Add a new method in `Element` class (lets call it method `do_something()`).
3. Under `do_something()`, write the Python code that will update the `Element` object when calling the method.
4. If the method does not need to send signals to JavaScript, then you can stop here, otherwise decorate `do_something()` by writing `@_ElementSignal()` above it.
5. Add a new method in `_ElementSignal` class in the beginning of `elements.py` and give it the same name as `do_something()`. Make this method a static method by adding the decorator `@staticmethod`.
6. Make sure that this static method has only `**kwargs` as a parameter and that it returns a dictionary with the following keys:
    - `func`: put here the name of the JavaScript function that you want to call (even if you did not create the JavaScript function yet). Lets call the function `_doSomethingJS()`
    - `args`: keep this as an empty list.
    - `kwargs`: this should be a dictionary that you want to pass to the JavaScript function.
7. In `_javascript_templates.py`, create a new function with the same name as the `func` you specified in the previous step (`_doSomethingJS()`). Make sure it has one parameter which is `kwargs`. Add the JavaScript code that you want to execute within it.
8. Add this function at the end of `_findAndExecute()` in an if-condition:
    ```javascript
    ...
    if (func == "_doSomethingJS") {
        _doSomethingJS(kwargs)
    }
    ```


### **Improve security**
If you found a security vulnerability, report it first **privately** in [GitHub](https://github.com/mubarakalmehairbi/ToUI/security) which is the preferred way or via email (mubarak.almehairbi1@gmail.com). Then we can discuss how to work on it. However, if there is no security vulnerability and you just want to provide an extra layer of security, you can contribute without reporting a security vulnerability.

### **Tests and examples**
In "examples" and "tests" folders, you can add new examples and tests to benefit the community. This is probably the most simple way to contribute to ToUI.

## Contributing steps
1. Create an [issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues) or contact the developer.
2. [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks) the repository.
3. Write and commit your changes in your fork.
4. Open a [pull request](https://docs.github.com/en/pull-requests).
