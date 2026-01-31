# @Time   : 2023-10-19
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import json
import itertools
from flask import Blueprint, Response, request
from hfwm.models.common import add_no_login_prefix, assert_condition
from hfwm.models.auth import auth_by_args, Auth
from hfwm.models.sse import get_conversation

sse_bp = Blueprint('sse', __name__, url_prefix='/wapi/sse')
conn = redis_conn({})


def subscribe_msg(channel, filter_):
    token = filter_['token']
    filter_.pop('token')
    pubsub = conn.pubsub()
    pubsub.subscribe('HFWM_SSE_PUBLISH' + channel)
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                if message['data'] == 'heartbeat' or message['data'] == b'heartbeat':
                    yield 'data: ' + json.dumps({"heart": "ok"}) + '\n\n'
                else:
                    flag = True
                    data = json.loads(message['data'])
                    if filter_ is not None:
                        for k, v in filter_:
                            if data.get(k) != v:
                                flag = False
                                break
                    if flag:
                        username = conn.get(token)
                        assert_condition(username is not None, 401, 'token 错误')
                        yield 'data: ' + json.dumps(data) + '\n\n'
    except GeneratorExit:  # 客户端断开连接
        log().info(f'Client disconnected from {channel}')
    finally:
        pubsub.unsubscribe('HFWM_SSE_PUBLISH' + channel)
        log().info(f'Unsubscribed from {channel}')
        pubsub.close()


def subscribe_msg_multiple(conversation_instances):
    try:
        streams = [instance.iter_lines() for instance in conversation_instances]
        for data_group in itertools.zip_longest(*streams, fillvalue=None):
            for idx, data in enumerate(data_group):
                if data is not None:  # 如果该实例有数据，推送
                    data['sseId'] = conversation_instances[idx].conversation_id
                    yield 'data: ' + json.dumps(data, ensure_ascii=False) + '\n\n'
        yield 'data: END\n\n'
    except GeneratorExit:  # 客户端断开连接
        log().error('multiple|Client disconnected')
    finally:
        log().info('multiple|Unsubscribed')


@sse_bp.route("/<topic>", methods=['GET'])
def sse(topic, _no_use=None):
    if topic != 'chat':
        data = auth_by_args()
        return Response(subscribe_msg(topic, data), mimetype="text/event-stream")
    data = dict(request.args)

    conversation_ids = data['conversationId'].replace('，', ',').split(',')
    ins_list = []
    for conversation_id in conversation_ids:
        conversation_instance = get_conversation(conversation_id)
        ins_list.append(conversation_instance)
    return Response(subscribe_msg_multiple(ins_list), mimetype="text/event-stream")


add_no_login_prefix('/wapi/sse/')
