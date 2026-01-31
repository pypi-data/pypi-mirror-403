# @Time   : 2023-08-02
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import relative_conf_path
import json
from flask import Blueprint, jsonify, request
from hfwm.models.common import assert_condition
from hfwm.models.databases.handle import DataHandle

setting_bp = Blueprint('setting', __name__, url_prefix='/wapi/setting')
with open(relative_conf_path('setting.json'), 'r') as f:
    setting_names = json.load(f)


@setting_bp.route('/<setting_name>', methods=['GET'])
def get_setting(setting_name, _no_use=None):
    assert_condition(setting_name in setting_names, 404, "不存在的配置")
    setting_table = DataHandle.get_table('setting')
    r = setting_table.find_one({'name': setting_name})
    if r is None:
        r = {}
    data = r.get('data')
    return jsonify({'code': 0, 'data': data, 'msg': ''})


@setting_bp.route('/<setting_name>/update', methods=['POST'])
def update_setting(setting_name, _no_use=None):
    data = request.get_json()
    data = data.get('data')
    assert_condition(setting_name in setting_names, 404, "不存在的配置")
    setting_table = DataHandle.get_table('setting')
    r = setting_table.update_one({'name': setting_name}, {'$set':{'data': data}}, upsert=True).modified_count
    return jsonify({'code': 0, 'data': r, 'msg': ''})