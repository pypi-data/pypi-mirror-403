# @Time   : 2023-06-23
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify, request, g
from hfwm.models.auth import Auth
from hfwm.models.databases.handle import DataHandle

cache_bp = Blueprint('cache', __name__, url_prefix='/wapi/cache')


@cache_bp.route('', methods=['GET'])
def get_cache():
    cache_table = DataHandle.get_table('cache')
    r = cache_table.find_one({'username': Auth.current().username})
    if r is None:
        return jsonify({'code': 0, 'data': Auth.current().info(), 'msg': ''})
    r['data'].update(Auth.current().info())
    return jsonify({'code': 0, 'data': r['data'], 'msg': ''})


@cache_bp.route('/update', methods=['POST'])
def update_cache():
    cache_table = DataHandle.get_table('cache')
    data = request.get_json()
    cache_table.update_one({'username': g.auth.username},
                           {'$set': {'data': data}}, upsert=True)

    return jsonify({'code': 0, 'data': data, 'msg': ''})
