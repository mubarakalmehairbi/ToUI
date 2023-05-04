# How ToUI works

## How ToUI creates web applications
ToUI uses [Flask](https://flask.palletsprojects.com/) to create web applications. To make the website responsive, ToUI communicates
with JavaScript through WebSockets. The WebSocket communication is established using the
Python package Flask-Sock and the JavaScript object `WebSocket`. JavaScript sends the
`document` object to Python along with other data while Python sends 'instructions' back to JavaScript:

![Python Javascript communication](images/communication.png)

## How ToUI creates desktop apps
ToUI uses [pywebview](https://pywebview.flowrl.com/) to create graphical user interfaces
(desktop apps). The communication between Python and JavaScript is similar to web apps
but using [js_api object](https://pywebview.flowrl.com/examples/js_api.html) in pywebview
instead of WebSockets.

## Security?
For web apps, ToUI uses Flask web framework, Flask-Sock for communicating through WebSockets,
and Flask-BasicAuth for restricting access to the website. To know more about the security of
these Python packages, please find their documentations below:
- [Flask docs](https://flask.palletsprojects.com/)
- [Flask-Sock docs](https://flask-sock.readthedocs.io/en/latest/)
- [Flask-BasicAuth docs](https://flask-basicauth.readthedocs.io/en/latest/)

ToUI uses pywebview for making desktop apps. To learn more about its security, please check
this link: [pywebview docs](https://pywebview.flowrl.com/). Note that pywebview can create 
two types of apps: serverless apps or apps built by running a local web server. However, 
ToUI currently creates only serverless pywebview apps.

## Instructions sent and received
ToUI receives data from JavaScript in the form of a JSON object. Below, the types of JSON objects
that ToUI receives from clients:
#### Page JSON
The most important JSON object. It contains the following keys:
```javascript
{type: 'page',
 func: ...,
 args: ...,
 url: ...,
 html: ...}
```
`type` is the type of JSON object, and it has the value 'page' when JavaScript sends the HTML document
as data. `func` contains the name of the Python function that should be called, `args` are the
arguments of this function, `url` is the URL of the HTML page that sent the data, `html`
is the HTML document itself as a string. In desktop applications, the key `url` does not exist.

#### Files information JSON
Another type of JSON object is a JSON that contains uploaded files:
```javascript
{type: 'files',
 files: ...}
```
`files` is a list of JSON objects that contain some information about each file:
```javascript
{name: ...,
size: ...,
'file-type': ...,
'last-modified': ...,
selector: ...,
`file-id`: ...}
```
`name` is the file name without the path, `size` is the size of file, `file-type` is the type of file,
`last-modified` is the last modified date as the number of milliseconds since the Unix epoch
(January 1, 1970 at midnight). `selector` is the CSS selector for the element that was used to upload
the files (`<input type="file">`). ToUI gives every uploaded file an id which is `file-id`. Depending
on whether the user asks for the content or not, the JSON might include the key `content` which
contains the content of the file

#### Saving file JSON
This JSON object is received after the user asks for a certain file to be saved using `File.save()` method.
```javascript
{type: "save files",
data: ...,
end: ...}
```
For every file saved, ToUI might receive this JSON object more than once. Each JSON object will contain a part
of the file content which is stored in the `data` key. `data` includes either a string or a list.
`end` is `false` until all the file content has been sent to ToUI.

Note that the structures of the JSON objects might change in future versions of
ToUI.