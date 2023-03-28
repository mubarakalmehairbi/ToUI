"""
Helper functions and logging.
"""
import warnings
import logging
import traceback

logger = logging.getLogger("ToUI")
logger.level = logging.INFO
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s:%(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def warn(msg):
    warnings.warn(message=msg, stacklevel=3)


def info(msg):
    logger.info(msg=msg)


def debug(msg):
    logger.debug(msg=msg)


def error(e:Exception):
    try:
        err = "".join(traceback.format_exception(e))
    except:
        err = e
    logger.error(msg=str(e))


def selector_to_str(tag_name=None, class_name=None, name=None, attrs=None):
    selectors = ""
    if tag_name:
        selectors += tag_name
    if class_name:
        selectors += f"[class=\"{class_name}\"]"
    if name:
        selectors += f"[name=\"{name}\"]"
    if attrs:
        for attr_key, attr_value in attrs.items():
            if attr_value:
                selectors += f"[{attr_key}=\"{attr_value}\"]"
    return selectors