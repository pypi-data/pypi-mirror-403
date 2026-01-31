# @Time   : 2023-06-21
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import redis_conn, log
import json
import pickle
from flask import request

conn = redis_conn({})


def get_set_resp_cache(resp_func, timeout):
    if request.method == 'GET':
        key = f'HFWM_HTTP_CACHE_GET_{request.url}'
    elif request.method == 'POST':
        key = f'HFWM_HTTP_CACHE_POST_{request.url} {json.dumps(request.get_json())}'
    else:
        raise Exception("内部错误，无法缓存")
    r = conn.get(key)
    if r is not None:
        # log().info(key[10:])
        return pickle.loads(r)
    r = resp_func()
    conn.setex(key, timeout, pickle.dumps(r))
    return r
