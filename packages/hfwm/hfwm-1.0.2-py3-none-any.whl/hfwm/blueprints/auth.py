# @Time   : 2023-06-23
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify
from hfwm.models.auth import *
from hfwm.utils.intercept_after_auth import add_route

auth_bp = Blueprint('auth', __name__, url_prefix='/wapi/auth')


@auth_bp.route('/login', methods=['POST'])
def wapi_login():
    data = request.get_json()
    username = str(data['username'])
    assert_condition('$' not in username, 401, "账号或密码错误")
    password = str(data['password'])
    expand = str(data.get('expand', '0'))
    log().info(f'{expand}login:{username}')
    if expand == '1':
        token = Auth.login_longtime(username, password)
    else:
        token = Auth.login(username, password)
    log().info(f'{expand}login_success:{username}')
    real_ip = request.headers.get('X-Real-IP', request.remote_addr)
    DataHandle.insert('oplog', {"oplogUser": username, "oplogType": "/wapi/auth/login", "oplogIp": real_ip})
    return jsonify({'code': 0, 'data': token, 'msg': ''})


@auth_bp.route('/logout', methods=['GET'])
def wapi_logout():
    token = request.headers.get('Authorization', '')
    Auth.logout(token)
    return jsonify({'code': 0, 'data': 'ok', 'msg': ''})


@auth_bp.route('/info', methods=['GET'])
def info():
    return jsonify({'code': 0, 'data': Auth.current().info(), 'msg': ''})


@auth_bp.route('/update_password', methods=['POST'])
def update_password():
    data = request.get_json()
    r = Auth.current().update_password(data.get('password', '')).modified_count
    return jsonify({'code': 0, 'data': r, 'msg': ''})


@add_route('/wapi/data/auth/update')
def auth_update():
    data = request.get_json()
    username = data['username']
    auth_new = Auth.load_by_username(username)
    if auth_new.username != Auth.current().username:
        assert_condition(not auth_new.is_super_admin, 401, '该用户的权限无法修改')
    nickname = data.get('nickname')
    roles = data.get('roles')
    password = data.get('password')
    r = 0
    if roles is not None:
        r += auth_new.update_roles(roles).modified_count
    if nickname is not None:
        r += auth_new.update_nickname(nickname).modified_count
    if password is not None:
        r += auth_new.update_password(password).modified_count
    if r > 1:
        r = 1
    return jsonify({'code': 0, 'data': r, 'msg': ''})


@add_route('/wapi/data/auth/insert')
def auth_insert():
    data = request.get_json()
    username = data['username']
    r = Auth.create_new(username, data.get('nickname', username), data.get('roles', []))
    return jsonify({'code': 0, 'data': str(r.upserted_id) if r.upserted_id is not None else '', 'msg': ''})


@add_route('/wapi/data/auth/remove')
def auth_remove():
    data = request.get_json()
    username = data['username']
    r = Auth.delete_auth(username)
    return jsonify({'code': 0, 'data': r.deleted_count, 'msg': ''})


add_no_login('/wapi/auth/login')
