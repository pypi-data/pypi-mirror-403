# @Time   : 2023-10-19
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import redis_conn, get_class_or_func
import json
import uuid
from hfwm.models.auth import Auth

conn = redis_conn({})

conversation_dict = {}


def publish_msg(channel, msg):
    conn.publish('HFWM_SSE_PUBLISH' + channel, json.dumps(msg))


def add_conversation(cls, kwargs, username=None):
    conversation_id = str(uuid.uuid4()).replace('-', '')
    class_path = cls.__module__ + '.' + cls.__name__
    conn.setex("conversation_" + conversation_id, 60, json.dumps({
        'conversationId': conversation_id,
        'username': username if username else Auth.current().username,
        'classPath': class_path,
        'kwargs': kwargs
    }))
    return conversation_id


def get_conversation(conversation_id):
    x = conn.get("conversation_" + conversation_id)
    if x is None:
        return None
    json_data = json.loads(x.decode('utf-8'))
    class_path = json_data['classPath']
    cls = get_class_or_func(class_path)
    conn.delete("conversation_" + conversation_id)
    ins = cls(**json_data['kwargs'])
    ins.conversation_id = conversation_id
    return ins
