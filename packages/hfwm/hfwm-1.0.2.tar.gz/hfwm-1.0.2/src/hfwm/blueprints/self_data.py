# @Time   : 2024-06-04
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify, request
from hfwm.models.databases.handle import DT, DataHandle
from hfwm.models.common import assert_condition
from hfwm.models.auth import bind_auth
from hfwm.utils.response_cache import get_set_resp_cache

self_data_bp = Blueprint('self_data', __name__, url_prefix='/wapi/self_data')


@self_data_bp.route('/<table_name>/<option>', methods=['POST'])
def wapi_data(table_name, option):
    assert_condition(table_name in DT.tables, 404, table_name)
    support_opts = ['find_one', 'find', 'count', 'group_count', 'calculate', 'insert', 'update', 'remove', 'upsert']
    assert_condition(option in support_opts, 404, option)
    data = request.get_json()
    bind_auth(table_name, data, option)
    if option in ['count', 'group_count', 'calculate']:
        r = get_set_resp_cache(lambda: getattr(DataHandle, option)(table_name, data), 5)
    else:
        r = getattr(DataHandle, option)(table_name, data)
    return jsonify({'code': 0, 'data': r, 'msg': ''})
