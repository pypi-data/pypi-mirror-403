# @Time   : 2025-05-29
# @Author : zhangxinhao
# @Compile : True
import sys


def read_env(tag):
    for arg in sys.argv[1:]:
        if arg.startswith(tag + '-'):
            return arg[len(tag) + 1:]
    return ''
