# @Time   : 2024-06-07
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
from redis.exceptions import RedisError

lua_script = '''
local count = tonumber(redis.call("GET", "HFW_UPLOAD_COUNT")) or 0
local new_count = (count + 1) % 1000
redis.call("SET", "HFW_UPLOAD_COUNT", new_count)
return new_count
'''

conn = redis_conn()
count_add_1 = conn.script_load(lua_script)


def get_counter():
    try:
        new_count = conn.evalsha(count_add_1, 0)
    except RedisError:
        conn.delete('HFW_UPLOAD_COUNT')
        new_count = conn.evalsha(count_add_1, 0)
    return new_count
