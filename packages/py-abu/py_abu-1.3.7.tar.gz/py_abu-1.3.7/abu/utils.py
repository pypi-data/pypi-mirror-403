# -*- coding: utf-8 -*-
# @Time    : 2024/8/7 18:42
# @Author  : Chris
# @Email   : 10512@qq.com
# @File    : utils.py
# @Software: PyCharm
import json
import threading
from types import SimpleNamespace
from collections.abc import Iterable

import pyperclip


def json_to_object(_json: dict | str) -> SimpleNamespace:
    return json.loads(_json if isinstance(_json, str) else json.dumps(_json),
                      object_hook=lambda d: SimpleNamespace(**d))


def set_timeout(func, delay, *args, **kwargs):
    timer = threading.Timer(delay, func, args, kwargs)
    timer.start()
    return timer


def set_clipboard_text(text: str) -> None:
    pyperclip.copy(text)


def get_clipboard_text() -> str:
    return pyperclip.paste()


def flatten_list(lst):
    """展开数组"""
    result = []
    for item in lst:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def set_cookie_to_chrome(cookiePath: str) -> str:
    """
    get cookie from curl_cffi to Chrome.
    :param cookiePath: 'F:\\AutoBackups\\Code\\PythonProjects\\temp\\90491@qq.com.cookie'
    :return: str
    """

    ret = (
        "function setCookie(cookieName,value,expiresTime,path){expiresTime=expiresTime||"
        '"Thu, 01-Jan-2030 00:00:01 GMT";path=path||"/";document.cookie=cookieName+"="+'
        '(value.includes("%")?value:encodeURIComponent(value))+"; expires="+expiresTime+"; path="+path;}'
    )
    with open(cookiePath, 'r') as f:
        cookies = json.load(f)
    for key, value in cookies.items():
        ret += f'setCookie(`{key}`,`{value}`);'
    set_clipboard_text(ret)
    return ret


if __name__ == '__main__':
    pass
