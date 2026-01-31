# @Time   : 2023-07-11
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify
from hfwm.models.databases.handle import DataHandle
from hfwm.utils.response_cache import get_set_resp_cache

enums_bp = Blueprint('enums', __name__, url_prefix='/wapi/enums')


@enums_bp.route('/<table_name>/<field>', methods=['GET'])
def wapi_enums(table_name, field):
    r = get_set_resp_cache(lambda: DataHandle.get_enums(table_name, {'field': field}), 30)
    return jsonify({'code': 0, 'data': r, 'msg': ''})
