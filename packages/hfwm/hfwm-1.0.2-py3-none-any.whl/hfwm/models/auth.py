# @Time   : 2023-06-18
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import json
import time
import hashlib
from flask import g, request
from hfwm.models.common import *
from hfwm.models.databases.handle import DataHandle, DT

auth_table = DataHandle.get_table('auth')
role_table = DataHandle.get_table('role')
super_admin_table = DataHandle.get_table('super_admin')
conn = redis_conn()


class Auth:

    def __init__(self, auth_info):
        self.username = auth_info['username']
        self.nickname = auth_info['nickname']
        self.roles = auth_info['roles']
        self.is_super_admin = auth_info['is_super_admin']
        self.perms = auth_info['perms']

    def info(self):
        return {
            'username': self.username,
            'nickname': self.nickname,
            'roles': self.roles,
            'perms': self.perms
        }

    def update_password(self, new_password):
        assert_condition(validate_password(new_password), 400, "密码长度6-30位")
        return auth_table.update_one({'username': self.username}, {'$set': {'password': new_password}}, upsert=False)

    def update_nickname(self, new_nickname):
        assert_condition(0 < len(new_nickname) < 20, 400, "昵称过长")
        return auth_table.update_one({'username': self.username}, {'$set': {'nickname': new_nickname}}, upsert=False)

    def update_roles(self, new_roles):
        for role in new_roles:
            assert_condition(role_table.find_one({'role': role}) is not None, 400, "角色不存在")
        return auth_table.update_one({'username': self.username}, {'$set': {'roles': new_roles}}, upsert=False)

    # 检查权限
    def check_perm_path(self, path):
        assert_condition(path not in get_denied_paths(), 400, "资源不存在")
        if len(get_allowed_paths()) > 0:
            assert_condition(path in get_allowed_paths(), 403, "无访问权限")
        # 如果是超级管理员,通过
        if self.is_super_admin:
            return

        perm_dict = get_perms()
        perm_name = perm_dict.get(path)

        if perm_name is None:
            return

        assert_condition(perm_name in self.perms, 403, "无此权限,联系管理员提升权限")

    # 检查权限名称
    def has_perm(self, name):
        return name in self.perms

    def set_current(self):
        g.auth = self

    @classmethod
    def current(cls) -> 'Auth':
        return g.auth

    @staticmethod
    def login(username, password):
        user_data = auth_table.find_one({'username': username})
        assert_condition((user_data is not None) and (user_data['password'] == password), 401, "账号或密码错误")
        s = "zf%.6f%s%s" % (time.time(), username, password)
        token = 'TK' + hashlib.md5(s.encode()).hexdigest()[:14]
        conn.set(token, username, 60 * 20)
        return token

    @staticmethod
    def login_longtime(username, password):
        user_data = auth_table.find_one({'username': username})
        assert_condition((user_data is not None) and (user_data['password'] == password), 401, "账号或密码错误")
        s = "zf%.6f%s%slongtime" % (time.time(), username, password)
        token = 'TK' + hashlib.md5(s.encode()).hexdigest() + hashlib.md5((s + s).encode()).hexdigest()[:30]
        conn.set(token, username, 60 * 60 * 24 * 7 + 60 * 60)
        return token

    @staticmethod
    def logout(token):
        token = str(token)
        assert_condition((len(token) == 16 or len(token) == 64) and token.startswith('TK'), 400, "错误的token")
        conn.delete(token)

    @classmethod
    def load_by_username(cls, username):
        assert_condition(isinstance(username, str) and len(username) > 0, 401, "用户名错误")
        auth_key = 'hfwm_auth_info_' + str(username)
        auth_info = conn.get(auth_key)
        if auth_info is not None:
            try:
                auth_info = json.loads(auth_info)
                instance = cls(auth_info)
                conn.expire(auth_key, 8)
                return instance
            except:
                conn.delete(auth_key)
        user_data = auth_table.find_one({'username': username})
        assert_condition(user_data is not None, 400, "用户不存在")
        username = user_data['username']
        roles = user_data.get('roles', [])
        nickname = user_data.get('nickname', username)
        is_super_admin = True if super_admin_table.find_one({'username': username}) is not None else False
        all_perms = []
        if is_super_admin:
            all_perms = get_perm_names()
        else:
            for role in roles:
                role_info = role_table.find_one({'role': role})
                if role_info is None:
                    continue
                perms = role_info.get('perms', [])
                if not isinstance(perms, list):
                    role_table.update_one({'role': role}, {'$set': {'perms': []}})
                    perms = []
                all_perms.extend(perms)
        auth_info = {
            'username': username,
            'nickname': nickname,
            'roles': roles,
            'is_super_admin': is_super_admin,
            'perms': list(set(all_perms))
        }
        auth_info_content = json.dumps(auth_info, ensure_ascii=False)
        conn.setex(auth_key, 8, auth_info_content)
        return cls(auth_info)

    @classmethod
    def load_by_token(cls, token):
        assert_condition((token is not None) and (5 <= len(token) <= 100), 401, 'token 错误')
        username = redis_conn().get(token)
        assert_condition(username is not None, 401, 'token 错误')
        username = username.decode()
        instance = cls.load_by_username(username)
        if len(token) == 16:
            conn.setex(token, 60 * 20, username)
        else:  # 64
            conn.setex(token, 60 * 60 * 24 * 7 + 60 * 60, username)
        return instance

    @classmethod
    def create_new(cls, username, nickname, roles):
        assert_condition(super_admin_table.find_one({'username': username}) is None, 400, "用户已存在")
        assert_condition(auth_table.find_one({'username': username}) is None, 400, "用户已存在")
        assert_condition(0 < len(username) < 20, 400, "用户名过长")
        assert_condition(0 < len(nickname) < 20, 400, "昵称过长")
        for role in roles:
            assert_condition(role_table.find_one({'role': role}) is not None, 400, "角色不存在")

        def make_password(username):
            password0 = 'hf-' + username + '-wm'
            password0 = hashlib.md5(password0.encode()).hexdigest()
            return password0[1:3] + password0[18:]

        return auth_table.update_one({"username": username},
                                     {'$setOnInsert':
                                          {"username": username, "password": make_password(username),
                                           'nickname': nickname,
                                           'roles': roles}}, upsert=True)

    @classmethod
    def delete_auth(cls, username):
        assert_condition(super_admin_table.find_one({'username': username}) is None, 400, "该用户无法删除")
        return auth_table.delete_one({'username': username})


def auth_by_args():
    data = dict(request.args)
    assert_condition('token' in data and len(data['token']) == 32, 401, '认证失败')
    token = data['token'][::2][::-1]
    Auth.load_by_token(token).set_current()
    Auth.current().check_perm_path(request.path)
    data['token'] = token
    return data


def bind_auth(table_name, data, option):
    username = Auth.current().username
    username_key = DT.get_username_key(table_name)
    assert_condition(username_key != '', 404, "不支持的操作")
    if option in ['find_one', 'insert', 'update', 'remove', 'upsert']:
        data[username_key] = username
    if option in ['find', 'count']:
        data.setdefault('equalCondition', {})
        data['equalCondition'][username_key] = username
    if option in ['group_count', 'calculate']:
        data.setdefault('query', {})
        data['query'].setdefault('equalCondition', {})
        data['query']['equalCondition'][username_key] = username
