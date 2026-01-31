# @Time   : 2025-07-16
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import json
import time
import hashlib
from flask import g, request
from hfwm.models.common import *
from hfwm.models.databases.handle import DataHandle, DT

app_table = DataHandle.get_table('app')
app_perms_dict = {}


class App:
    def __init__(self, appInfo):
        self.app_key = appInfo['appKey']
        self.app_id = appInfo['appId']
        self.app_user = appInfo['appUser']
        self.app_status = appInfo['appStatus']
        self.app_type = appInfo['appType']
        self.app_info = appInfo.get('appInfo', {})
        self.app_parent = appInfo.get('appParent', '')

    def info(self):
        return {
            'appKey': self.app_key,
            'appId': self.app_id,
            'appUser': self.app_user,
            'appStatus': self.app_status,
            'appType': self.app_type,
            'appInfo': self.app_info
        }

    def set_current(self):
        g.app = self

    @classmethod
    def current(cls) -> 'App':
        return g.app

    @classmethod
    def load_by_token(cls, token):
        assert_condition(token.startswith('Bearer '), 401, '认证失败')
        app_key = token.split(' ')[-1]
        app_key = app_key.replace(' ', '').replace('{', '').replace('}', '')
        assert_condition(len(app_key) > 10, 401, 'auth 认证失败')
        app_info = DataHandle.find_one('app', {'appKey': app_key})
        assert_condition(app_info is not None, 401, 'auth 认证失败')
        return cls(app_info)

    @classmethod
    def load_by_app_key(cls, app_key):
        app_info = DataHandle.find_one('app', {'appKey': app_key})
        assert_condition(app_info is not None, 401, 'appKey 不存在')
        return cls(app_info)

    @classmethod
    def create_app(cls, app_id, app_user='test', app_status='开启', app_type='app', app_info=None, random_key='',
                   app_parent=''):
        app_key = 'sk-' + cal_str_md5('app：' + app_id + random_key)
        app = DataHandle.find_one('app', {'appKey': app_key})
        if app is not None:
            log().info(f'{app_id} 已创建')
            return app
        app = {
            'appKey': app_key,
            'appId': app_id,
            'appUser': app_user,
            'appStatus': app_status,
            'appType': app_type,
            'appInfo': {} if app_info is None else app_info
        }
        if app_parent:
            app['appParent'] = app_parent
        DataHandle.insert('app', app)
        log().info(f'{app_id} 创建成功')
        return app

    @staticmethod
    def add_perm(path, app_types):
        if path in app_perms_dict:
            raise Exception(f'app add perm:{path}, 重复添加')
        app_perms_dict[path] = app_types

    def check_perm_path(self, path):
        assert_condition(path not in get_denied_paths(), 404, "资源不存在")
        if len(get_allowed_paths()) > 0:
            assert_condition(path in get_allowed_paths(), 403, "无访问权限")
        if self.app_type == 'admin':
            return

        # 未配置权限的默认不通过
        assert_condition(app_perms_dict.get(path) is not None, 404, "无法访问")

        assert_condition(self.app_type in app_perms_dict[path], 403, "无权限")
