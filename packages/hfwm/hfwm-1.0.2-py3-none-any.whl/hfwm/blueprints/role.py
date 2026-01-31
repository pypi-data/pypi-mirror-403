# @Time   : 2023-06-23
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify, request
from hfwm.models.common import *
from hfwm.models.databases.handle import DataHandle

role_bp = Blueprint('role', __name__, url_prefix='/wapi/role')


@role_bp.route('/list', methods=['GET'])
def get_roles():
    db_roles_item = DataHandle.get_table('role').find({})
    db_roles = []
    for it in db_roles_item:
        it.pop('_id')
        db_roles.append(it)

    return jsonify({'code': 0, 'data': db_roles, 'msg': ''})


@role_bp.route('/get', methods=['POST'])
def get_role_perms():
    data = request.get_json()
    role = data['role']
    role_info = DataHandle.get_table('role').find_one({'role': role})
    assert_condition(role_info is not None, 400, "查询的角色不存在")
    perms = role_info.get('perms', [])
    perms.sort()
    return jsonify({'code': 0, 'data': perms, 'msg': ''})


@role_bp.route('/insert', methods=['POST'])
def insert_role():
    data = request.get_json()
    role = data['role']
    perms = data['perms']
    for perm in perms:
        assert_condition(perm in get_perm_names(), 400, f"未定义的 {perm}")
    r = DataHandle.get_table('role').update_one({'role': role}, {'$setOnInsert': {'perms': perms}}, upsert=True).modified_count
    return jsonify({'code': 0, 'data': r, 'msg': ''})


@role_bp.route('/update', methods=['POST'])
def update_role():
    data = request.get_json()
    role = data['role']
    perms = data['perms']
    for perm in perms:
        assert_condition(perm in get_perm_names(), 400, f"未定义的 {perm}")
    r = DataHandle.get_table('role').update_one({'role': role}, {'$set': {'perms': perms}}, upsert=False).modified_count
    return jsonify({'code': 0, 'data': r, 'msg': ''})


@role_bp.route('/remove', methods=['POST'])
def remove_role():
    data = request.get_json()
    count = DataHandle.count('auth', {'inCondition': {'roles': [data['role']]}})
    if count == 0:
        r = DataHandle.get_table('role').delete_one({'role': data['role']}).deleted_count
    else:
        raise Exception("无法删除已被分配的角色")
    return jsonify({'code': 0, 'data': r, 'msg': ''})


@role_bp.route('/mark', methods=['POST'])
def mark_role():
    data = request.get_json()
    role = data['role']
    mark = data['mark'].strip()
    assert_condition(len(mark) < 300, 400, "角色说明过长")
    r = DataHandle.get_table('role').update_one({'role': role}, {'$set': {'mark': mark}}, upsert=False).modified_count
    return jsonify({'code': 0, 'data': r, 'msg': ''})
