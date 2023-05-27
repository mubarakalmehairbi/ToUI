# How ToUI works

## How ToUI creates applications
ToUI uses [Flask](https://flask.palletsprojects.com/) to create web and desktop applications. To make the app responsive, ToUI communicates with JavaScript through WebSockets. The WebSocket communication is established using the Python package Flask-Sock and the JavaScript object `WebSocket`. JavaScript sends the `document` object to Python along with other data while Python sends 'instructions' back to JavaScript:

![Python Javascript communication](images/communication.png)

Note that you can still use HTTP requests to communicate with ToUI. Check `Page.on_url_request` method. However, the primary focus of ToUI is on WebSockets communication, so there might be some methods in ToUI that will not work when you call them within HTTP requests.

For desktop applications, ToUI uses also [pywebview](https://pywebview.flowrl.com/). In the old versions of ToUI (version 1.x.x), ToUI was using [js_api object](https://pywebview.flowrl.com/examples/js_api.html) primarly for communicating in desktop applications, but currently it relies more on WebSockets.

## Security?
For both web apps and desktop apps, ToUI uses Flask web framework, Flask-Sock for communicating through WebSockets, and other flask extensions. To know more about the security of these Python packages, please find their documentations below:
- [Flask docs](https://flask.palletsprojects.com/)
- [Flask-Sock docs](https://flask-sock.readthedocs.io/en/latest/)
- [Flask-Session docs](https://flask-session.readthedocs.io/en/latest/)
- [Flask-Caching docs](https://flask-caching.readthedocs.io/en/latest/)
- [Flask-BasicAuth docs](https://flask-basicauth.readthedocs.io/en/latest/)
- [Flask-Login docs](https://flask-login.readthedocs.io/en/latest/)
- [Flask-SQLAlchemy docs](https://flask-sqlalchemy.palletsprojects.com/)

ToUI uses pywebview for making desktop apps. To learn more about its security, please check this link: [pywebview docs](https://pywebview.flowrl.com/). Note that pywebview can create two types of apps: serverless apps or apps built by running a local web server. In the old versions of ToUI (version 1.x.x), it was creating serverless pywebview apps, but currently ToUI creates Flask-based apps.

Check methods: <a href="./toui.apps.Website.set_data_validation.html">`Website.set_data_validation`</a> and <a href="./toui.apps.Website.set_ws_validation.html">`Website.set_ws_validation`</a> for possible security improvements.


> ⚠️ **Warning**
> 
> The versions v2.0.1 to v2.4.0 contain a security vulnerability. You can read about it [here](https://github.com/mubarakalmehairbi/ToUI/security/advisories/GHSA-hh7j-pg39-q563).  Please use them with caution or upgrade to v2.4.1.

## Instructions sent and received
ToUI receives data from JavaScript in the form of a JSON object. Below, the types of JSON objects that ToUI receives from clients:

#### Page JSON
The most important JSON object. It contains the following keys:
```json
{"type": "page",
 "func": ...,
 "args": ...,
 "selector-to-element": ...,
 "url": ...,
 "html": ...,
 "uid": ...}
```
`type` is the type of JSON object, and it has the value 'page' when JavaScript sends the HTML document as data. `func` contains the name of the Python function that should be called, `args` are the arguments of this function, `selector-to-element` is a boolean that is only true if one of the arguments is an HTML element, `url` is the URL of the HTML page that sent the data, `html` is the HTML document itself as a string. `uid` is the id of the window when creating desktop apps.
If one of the argument is an HTML element, it will be converted to a JSON that contains its CSS selector:
```json
{"type": "element",
 "selector": ...}
```

#### Files information JSON
Another type of JSON object is a JSON that contains uploaded files:
```json
{"type": "files",
 "files": ...,
 "msg-num": ...}
```
`msg-num` is the ID of message, `files` is a list of JSON objects that contain some information about each file:
```json
{"name": ...,
 "size": ...,
 "file-type": ...,
 "last-modified": ...,
 "selector": ...,
 "file-id": ...
```
`name` is the file name without the path, `size` is the size of file, `file-type` is the type of file, `last-modified` is the last modified date as the number of milliseconds since the Unix epoch (January 1, 1970 at midnight). `selector` is the CSS selector for the element that was used to upload the files (`<input type="file">`). ToUI gives every uploaded file an id which is `file-id`. Depending on whether the user asks for the content or not, the JSON might include the key `content` which contains the content of the file.

#### Saving file JSON
This JSON object is received after the user asks for a certain file to be saved using `File.save()` method.
```javascript
{"type": "save files",
 "data": ...,
 "end": ...,
 "msg-num": ...}
```
For every file saved, ToUI might receive this JSON object more than once. Each JSON object will contain a part of the file content which is stored in the `data` key. `data` includes either a string or a list. `end` is `false` until all the file content has been sent to ToUI.

Note that the structures of the JSON objects might change in future versions of
ToUI.
