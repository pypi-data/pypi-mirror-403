# @Time   : 2023-07-12
# @Author : zhangxinhao
# @Compile : True

_funcs = {}


def add_func(url, func):
    if url in _funcs:
        raise Exception(f'add_func {url}已添加')
    _funcs[url] = func


def add_route(url):
    def decorator(f):
        add_func(url, f)
        return f

    return decorator


def remove_func(url):
    _funcs.pop(url)


def get_func(url):
    return _funcs.get(url)
