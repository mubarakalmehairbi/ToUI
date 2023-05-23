"""
JavaScript code that is added to HTML files.
"""
template = """
var conn = "wss"
if (location.protocol == "http:") {
    conn = "ws"
}
const socket = new WebSocket(conn + '://' + location.host + '/toui-communicate')
socket.addEventListener('message', ev => {
    _findAndExecute(ev.data)
  });

const urlPath = location.pathname
const _appType = "{app_type}"
_touiFiles = {}
_pywebviewIsLoaded = false
async function _toPy(...args) {
    var func = args.shift()
    if (_appType === "DesktopApp" && _pywebviewIsLoaded == false) {
        await _waitForPywebview()
    }

    var selector_to_element = false
    for (var i = 0; i < args.length; i++) {
        if (args[i] instanceof HTMLElement) {
            args[i] = {type: "element",
                       selector: _getElementSelector(args[i])}
            selector_to_element = true
        }
    }

    var json = {type: "page",
                func: func,
                args: args,
                "selector-to-element": selector_to_element,
                url: urlPath}
    _manageProperties()
    json['html'] = _getDoc()
    json['uid'] = await _getUid()
    var jsonstring = JSON.stringify(json)
    if (socket.readyState === 0) {
        socket.onopen = async function() {
            socket.send(jsonstring);
        }
    } else {
        socket.send(jsonstring)
    }
}

async function _getUid() {
    try {
        const uid = await pywebview.api.get_uid()
        return uid
    } catch (err) {
        const uid = null
        return null
    }
}

window.addEventListener('pywebviewready', function () {
    _pywebviewIsLoaded = true
})

function _waitForPywebview() {
  return new Promise(function (resolve, reject) {
    window.addEventListener('pywebviewready', function () {
      resolve()
      _pywebviewIsLoaded = true
    })
  })
}

function _send(jsonstring) {
    socket.send(jsonstring)
}

function _getDoc() {
    var serializer = new XMLSerializer()
    const doc = serializer.serializeToString(document)
    return doc
    }

function _setDoc(kwargs) {
    document.open()
    document.write(kwargs['doc'])
    document.close()
    }
    
async function _manageProperties() {
    var properties = {files: []}
    var input_elements = document.getElementsByTagName("input")
    for (var input_element of input_elements) {
        input_element.setAttribute("value", input_element.value)
        if (input_element.checked == true) {
            input_element.setAttribute("checked", "")
        } else {
            input_element.removeAttribute("checked")
        }
    }

    var textarea_elements = document.getElementsByTagName("textarea")
    for (var textarea_element of textarea_elements) {
        textarea_element.setAttribute("value", textarea_element.value)
        }

    var select_elements = document.getElementsByTagName("select")
    for (var select_element of select_elements) {
        select_element.setAttribute("value", select_element.value)
        for (var i = 0; i < select_element.options.length; i++) {
            option = select_element.options[i]
            if (i == select_element.selectedIndex) {
                option.setAttribute("selected", "")
            } else {
                option.removeAttribute("selected")
            }
        }
    }
    return properties
}

async function _getFiles(kwargs) {
    var files = []
    var element = _getElement(kwargs['selector'])
    if (element.type == "file") {
        for (var file of element.files) {
            var selector = _getElementSelector(element)
            var fileJSON = {name: file.name,
                             size: file.size,
                             'file-type': file.type,
                             'last-modified': file.lastModified,
                             selector: selector}
            if (kwargs['with_content'] == true) {
                await file.text().then(function (text) {
                    fileJSON['content'] = text
                })
            }
            var keys = Object.keys(_touiFiles)
            var newKey = 0
            if (keys.length != 0) {
                var lastKey = keys.sort().reverse()[0]
                const newKey = parseInt(lastKey) + 1
            }
            _touiFiles[newKey.toString()] = file
            fileJSON['file-id'] = newKey.toString()
            files.push(fileJSON)
        }
    }
    var jsonString = JSON.stringify({data: files, type: "files"})
    var dataSent = _send(jsonString)
    return dataSent
}

async function _saveFile(kwargs) {
    var fileId = kwargs['file-id']
    var file = _touiFiles[fileId]
    var reader = new FileReader()
    if (kwargs['binary'] == true) {
        reader.onload = function () {
            const buffer = reader.result
            const content = new Uint8Array(buffer)
            const lengthPerPart = 16000
            const charsLength = content.length
            for (var i = 0; i < charsLength; i += lengthPerPart) {
                var smallerContent = [...content.slice(i, i + lengthPerPart)]
                var jsonString = JSON.stringify({type: "save files",
                                                  data: smallerContent,
                                                  end: false})
                var dataSent = _send(jsonString)
            }
            var jsonString = JSON.stringify({type: "save files", data: [],
                                              end: true})
            var dataSent = _send(jsonString)
        }
        reader.readAsArrayBuffer(file)
    } else {
        reader.onload = function () {
            const content = reader.result
            const lengthPerPart = 16000
            const charsLength = content.length
            for (var i = 0; i < charsLength; i += lengthPerPart) {
                var smallerContent = content.substring(i, i + lengthPerPart)
                var jsonString = JSON.stringify({type: "save files",
                                                  data: smallerContent,
                                                  end: false})
                var dataSent = _send(jsonString)
            }
            var jsonString = JSON.stringify({type: "save files", data: "",
                                              end: true})
            var dataSent = _send(jsonString)
        }
        reader.readAsText(file)
    }
}
    
function _getElement(selector) {
    const element = document.querySelector(selector)
    return element
}

var _getElementSelector = function(el) {
  if (!(el instanceof Element))
            return;
        var path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            var selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break;
            } else {
                var sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() == selector)
                       nth++;
                }
                if (nth != 1)
                    selector += ":nth-of-type("+nth+")";
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        path = path.join(" > ");
        return path;
     }

function _replaceElement(kwargs) {
    var old_element = _getElement(kwargs['selector'])
    old_element.outerHTML = kwargs['element']
    }

function _replaceElements(kwargs) {
    var elements = document.querySelectorAll(kwargs['selectors'])
    var pyelements = kwargs['elements']
    for (i = 0; i < elements.length; i++) {
        elements[i].outerHTML = pyelements[i];
        }
    }
    
function _setAttr(kwargs) {
    var element = _getElement(kwargs['selector'])
    element.setAttribute(kwargs['name'], kwargs['value'])
    if (kwargs['name'] == 'value') {
        element.value = kwargs['value']
    }
    if (kwargs['name'] == 'checked') {
        element.checked = kwargs['value']
    }
}

function _delAttr(kwargs) {
    var element = _getElement(kwargs['selector'])
    element.removeAttribute(kwargs['name'])
    if (kwargs['name'] == 'checked') {
        element.checked = false
    }
}

function _setContent(kwargs) {
    var element = _getElement(kwargs['selector'])
    element.innerHTML = kwargs['content']
}

function _addContent(kwargs) {
    var element = _getElement(kwargs['selector'])
    element.insertAdjacentHTML("beforeend" ,kwargs['content'])
}

function _addScript(kwargs) {
    const script = kwargs['script']
    var new_element = document.createElement('script')
    new_element.innerHTML = script
    document.body.appendChild(new_element)
    }
    
function _goTo(kwargs) {
    const url = kwargs['url']
    const newTab = kwargs['new']
    if (newTab == true) {
        window.open(location.origin + url)
    } else {
        window.open(location.origin + url, "_self")
    }
}

function _resizeEmbed(element) {
    element.height = 0
    element.width = 0
    element.style.height = element.contentWindow.document.body.scrollHeight + 1 + 'px'
    element.style.width = element.contentWindow.document.body.scrollWidth + 1 + 'px'
}

function _getKey(kwargs) {
    const value = localStorage.getItem(kwargs['key'])
}

function _setKey(kwargs) {
    localStorage.setItem(kwargs['key'], kwargs['value'])
}

function _delKey(kwargs) {
    localStorage.removeItem(kwargs['key'])
}

function _setDefaults(kwargs) {
    const touiVars = localStorage.getItem(kwargs['key'])
    if (touiVars == null) {
        localStorage.setItem("toui-vars", kwargs['default-vars'])
    }
}

function _findAndExecute(jsonString) {
    var instructions = JSON.parse(jsonString)
    var func = instructions['func']
    var kwargs = instructions['kwargs']
    if (func == "_replaceElement") {
        _replaceElement(kwargs)
    }
    if (func == "_replaceElements") {
        _replaceElements(kwargs)
    }
    if (func == "_setAttr") {
        _setAttr(kwargs)
    }
    if (func == "_delAttr") {
        _delAttr(kwargs)
    }
    if (func == "_setContent") {
        _setContent(kwargs)
    }
    if (func == "_addContent") {
        _addContent(kwargs)
    }
    if (func == "_setDoc") {
        _setDoc(kwargs)
    }
    if (func == "_addScript") {
        _addScript(kwargs)
    }
    if (func == "_goTo") {
        _goTo(kwargs)
    }
    if (func == "_getFiles") {
        _getFiles(kwargs)
    }
    if (func == "_saveFile") {
        _saveFile(kwargs)
    }
    if (func == "_getKey") {
        _getKey(kwargs)
    }
    if (func == "_setKey") {
        _setKey(kwargs)
    }
    if (func == "_delKey") {
        _delKey(kwargs)
    }
    if (func == "_setDefaults") {
        _setDefaults(kwargs)
    }
}"""

def custom_func(name):
    text = f"""
    function {name}(...args) {{
        _toPy('{name}', ...args)
    }}
    """
    return text


def get_script(app_type='Website'):
    script = template.replace('{app_type}', app_type)
    return script
