# @Time   : 2023-07-27
# @Author : zhangxinhao
# @Compile : True
from hfwm.models.databases.handle import DataHandle


class Perm:
    def __init__(self, perm):
        self.perm = perm

    def get_all_roles(self):
        items = DataHandle.get_table('role').find({"perms": self.perm})
        r = []
        for it in items:
            r.append(it['role'])
        return r

    def get_all_users(self):
        roles = self.get_all_roles()
        items = DataHandle.get_table('auth').find({"roles":{'$in': roles}})
        r = []
        for it in items:
            r.append(it['username'])
        return r


# class Role:
#     def __init__(self, ):

# def

# 获取含有某个权限的所有角色


# 获取含有某个权限的所有用户
