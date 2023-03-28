"""
JavaScript code that is added to HTML files.
"""
web_template = f"""
var conn = "wss"
if (location.protocol == "http:") {{
    conn = "ws"
}}
const socket = new WebSocket(conn + '://' + location.host + '/toui-communicate')
socket.addEventListener('message', ev => {{
    _findAndExecute(ev.data)
  }});
const urlPath = location.pathname
function _toPy(...arguments) {{
    var func = arguments.shift()
    var json = {{func:func,
                args: arguments,
                url: urlPath}}
    json['html'] = _getDoc()
    var jsonstring = JSON.stringify(json)
    if (socket.readyState === 0) {{
        socket.onopen = function() {{
            socket.send(jsonstring);
        }}
    }} else {{
        socket.send(jsonstring)
    }}
}}

"""
    
    
desktop_template = f"""
function _toPy(...arguments) {{
    var func = arguments.shift()
    var json = {{func:func,
                args: arguments}}
    json['html'] = _getDoc()
    var jsonstring = JSON.stringify(json)
    pywebview.api.communicate(jsonstring)
}}
"""


common_template = f"""
function _getDoc() {{
    var input_elements = document.getElementsByTagName("input")
    for (var input_element of input_elements) {{
        input_element.setAttribute("value", input_element.value)
        input_element.setAttribute("checked", input_element.checked)
    }}
    var serializer = new XMLSerializer()
    const doc = serializer.serializeToString(document)
    return doc
    }}

function _setDoc(kwargs) {{
    document.open()
    document.write(kwargs['doc'])
    document.close()
    }}
    
function _getElement(kwargs) {{
    var number = 0
    if ('number' in kwargs) {{
        var number = parseInt(kwargs['number'])
    }}
    if ('parent' in kwargs) {{
        const parent = _getElement(kwargs['parent'])
        const element = parent.querySelectorAll(kwargs['selector'])[number]
        return element
    }} else {{
        const elements = document.querySelectorAll(kwargs['selector'])
        const element = elements[number]
        return element
    }}
}}

function _replaceElement(kwargs) {{
    var old_element = _getElement(kwargs['selector'])
    old_element.outerHTML = kwargs['element']
    }}

function _replaceElements(kwargs) {{
    var elements = document.querySelectorAll(kwargs['selectors'])
    var pyelements = kwargs['elements']
    for (i = 0; i < elements.length; i++) {{
        elements[i].outerHTML = pyelements[i];
        }}
    }}
    
function _setAttr(kwargs) {{
    var element = _getElement(kwargs['selector'])
    element.setAttribute(kwargs['name'], kwargs['value'])
    if (kwargs['name'] == 'value') {{
        element.value = kwargs['value']
    }}
    if (kwargs['name'] == 'checked') {{
        element.checked = kwargs['value']
    }}
}}

function _setContent(kwargs) {{
    var element = _getElement(kwargs['selector'])
    element.innerHTML = kwargs['content']
}}

function _addContent(kwargs) {{
    var element = _getElement(kwargs['selector'])
    element.insertAdjacentHTML("beforeend" ,kwargs['content'])
}}

function _addScript(kwargs) {{
    const script = kwargs['script']
    var new_element = document.createElement('script')
    new_element.innerHTML = script
    document.body.appendChild(new_element)
    }}
    
function _goTo(kwargs) {{
    const url = kwargs['url']
    location.href = location.origin + url
}}

function _resizeEmbed(element) {{
    element.height = 0
    element.width = 0
    element.style.height = element.contentWindow.document.body.scrollHeight + 1 + 'px'
    element.style.width = element.contentWindow.document.body.scrollWidth + 1 + 'px'
}}

function _findAndExecute(jsonString) {{
    var instructions = JSON.parse(jsonString)
    var func = instructions['func']
    var kwargs = instructions['kwargs']
    if (func == "_replaceElement") {{
        _replaceElement(kwargs)
    }}
    if (func == "_replaceElements") {{
        _replaceElements(kwargs)
    }}
    if (func == "_setAttr") {{
        _setAttr(kwargs)
    }}
    if (func == "_setContent") {{
        _setContent(kwargs)
    }}
    if (func == "_addContent") {{
        _addContent(kwargs)
    }}
    if (func == "_setDoc") {{
        _setDoc(kwargs)
    }}
    if (func == "_addScript") {{
        _addScript(kwargs)
    }}
    if (func == "_goTo") {{
        _goTo(kwargs)
    }}
}}"""

def custom_func(name):
    text = f"""
    function {name}(...args) {{
        _toPy('{name}', ...args)
    }}
    """
    return text


def get_script(app_type='web'):
    if app_type == "desktop":
        template = desktop_template
    else:
        template = web_template
    script = template + common_template
    return script
