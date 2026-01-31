# @Time   : 2023-09-19
# @Author : zhangxinhao
# @Compile : True
_checkers = {}


def value_wrap(r, value):
    if r is None:
        return value
    return r

# bug 只要同名字段全局生效
def add_checker(field, checker, *args):
    _checkers[field] = lambda value: value_wrap(checker(field, value, *args), value)


def get_checker(field):
    if _checkers.get(field) is None:
        return lambda value: value
    return _checkers.get(field)
