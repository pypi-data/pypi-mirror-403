# @Time   : 2023-07-26
# @Author : zhangxinhao
# @Compile : True
import re
from flask import abort

_perm_dict = {}
_no_login = set()
_no_login_prefix = []
_perm_names = []
_denied_paths = set()
_allowed_paths = set()


# path唯一
def add_perm(name, path=None):
    if not isinstance(path, list):
        paths = [path]
    else:
        paths = path

    for path in paths:
        if path is None:
            path = "tag/" + name.replace(":", "/")
        if path in _perm_dict:
            raise Exception(f"{path}重复配置")
        _perm_dict[path] = name
        if name not in _perm_names:
            _perm_names.append(name)
            _perm_names.sort()


def add_denied_path(path):
    if not isinstance(path, list):
        paths = [path]
    else:
        paths = path
    for path in paths:
        if path in _denied_paths:
            raise Exception(f"denied  {path}重复配置")
        _denied_paths.add(path)


def add_allowed_path(path):
    if not isinstance(path, list):
        paths = [path]
    else:
        paths = path
    for path in paths:
        if path in _allowed_paths:
            raise Exception(f"allowed  {path}重复配置")
        _allowed_paths.add(path)


def get_perms():
    return _perm_dict


def get_denied_paths():
    return _denied_paths


def get_allowed_paths():
    return _allowed_paths


def get_perm_names():
    return _perm_names


def add_no_login(path):
    _no_login.add(path)


def add_no_login_prefix(path):
    _no_login_prefix.append(path)


def is_no_login(path):
    if path in _no_login:
        return True
    for p in _no_login_prefix:
        if path.startswith(p):
            return True
    return False


'''
404 错误资源
403 权限不够
401 未登录
400 错误的请求，比如参数错误
500 其他错误
'''


def assert_condition(condition, code, desc=''):
    if not condition:
        abort(code, desc)


def validate_password(password):
    pattern = r"^[A-Za-z\d@$!%*?&#^=+-]{6,30}$"
    return bool(re.match(pattern, password))


def refuse_other_opts(table_name, opts):
    support_opts = ['find_one', 'find', 'count', 'group_count', 'calculate', 'insert', 'update', 'remove', 'upsert']
    for opt in support_opts:
        if opt not in opts:
            add_denied_path(f'/wapi/data/{table_name}/{opt}')
