"""
A module that creates instructions "signals" to allow communicating with JavaScript.
"""
import inspect
import json
from toui._helpers import debug
from copy import copy
from functools import wraps


class Signal:

    included_private_methods = ["_open_another_page"]
    no_return_functions = []

    def __init__(self):
        self.ws = None

    def __call__(decorator, func):
        decorator._func = func
        @wraps(func)
        def new_func(self, *args, **kwargs):
            decorator.object = self
            if self._signal_mode:
                original_copy = copy(self)
            value = decorator._func(self, *args, **kwargs)
            if self._signal_mode:
                if self.__class__.__name__ == 'Element':
                    decorator.ws = self._parent_page.__dict__.get("_ws")
                    decorator.evaluate_js = self._parent_page._evaluate_js
                elif self.__class__.__name__ == "Page":
                    decorator.ws = self.__dict__.get("_ws")
                    decorator.evaluate_js = self._evaluate_js
                kwargs = inspect.signature(decorator._func).bind(self, *args, **kwargs)
                kwargs.apply_defaults()
                kwargs = kwargs.arguments
                kwargs['return_value'] = value
                kwargs['object'] = kwargs['self']
                kwargs['original_copy'] = original_copy
                del kwargs['self']
                decorator._call_method(decorator._func, **kwargs)
            if func.__name__ in decorator.no_return_functions:
                return
            return value
        return new_func

    def _call_method(self, func, **kwargs):
        for method_name, method in inspect.getmembers(self, inspect.isfunction):
            if method_name == func.__name__ and (not method_name.startswith("_") or
                                                 method_name in self.included_private_methods):
                signal = method(**kwargs)
                if signal:
                    return self._send(signal)
                else:
                    return

    def _send(self, signal):
        debug(f"SENT: {signal}")
        if self.ws:
            self.ws.send(json.dumps(signal))
        else:
            self.evaluate_js(func=signal['func'], kwargs=signal['kwargs'])
