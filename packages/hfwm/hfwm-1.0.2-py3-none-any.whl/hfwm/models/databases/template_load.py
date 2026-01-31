# @Time   : 2023-09-14
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import os
import json
from collections import Counter


def get_duplicates(lst):
    count = Counter(lst)
    return [item for item in count if count[item] > 1]


def get_first_word(camel_case_string):
    for i in range(1, len(camel_case_string)):
        if camel_case_string[i].isupper():
            return camel_case_string[:i]
    return camel_case_string


auth_config = {
    "fieldKeys": ["field", "type", "desc", "enumValues"],
    "fields": [
        ["username", "string", "用户名(id)"],
        ["password", "string", "用户密码"],
        ["nickname", "string", "用户名(昵称)"],
        ["roles", "list_string", "角色列表"]
    ],
    "allowNoneFields": ['password', 'nickname', 'roles'],
    "hiddenFields": ['password'],
    "indexes": ["username"],
    "groupCountFields": [],
    "parents": [],
    "tableName": "用户"
}

os.makedirs('/tmp/hfwm_tables', exist_ok=True)
os.makedirs(relative_conf_path('.auto_tables'), exist_ok=True)

with open("/tmp/hfwm_tables/auth.json", 'w') as f:
    json.dump(auth_config, f, ensure_ascii=False)

oplog = {
    "fieldKeys": ["field", "type", "desc", "enumValues"],
    "fields": [
        ["oplogId", "id", "id"],
        ["oplogUser", "string", "用户名(id)"],
        ["oplogType", "string", "操作类型"],
        ["oplogIp", "string", "操作ip"]
    ],
    "allowNoneFields": ["oplogIp"],
    "hiddenFields": [],
    "indexes": ["oplogId"],
    "groupCountFields": ['oplogType', 'oplogUser'],
    "parents": [],
    "tableName": "操作记录"
}

with open("/tmp/hfwm_tables/oplog.json", 'w') as f:
    json.dump(oplog, f, ensure_ascii=False)

autopage = {
    "fieldKeys": ["field", "type", "desc", "enumValues"],
    "fields": [
        ["autopageId", "id", "页面id"],
        ["autopageUser", "username", "用户名(id)"],
        ["autopageName", "string", "自动查询页面名"],
        ["autopageConfig", "any", "页面配置"],
    ],
    "allowNoneFields": [],
    "hiddenFields": [],
    "indexes": ["autopageId"],
    "groupCountFields": [],
    "parents": [],
    "editFields": ["autopageName", "autopageConfig"],
    "tableName": "自动生成页面"
}

with open("/tmp/hfwm_tables/autopage.json", 'w') as f:
    json.dump(autopage, f, ensure_ascii=False)

app_t = {
    "fieldKeys": ["field", "type", "desc", "enumValues"],
    "fields": [
        ["appKey", "string", "应用认证"],
        ["appId", "string", "应用id"],
        ["appUser", "string", "应用关联用户"],
        ["appStatus", "enum", "是否开启", "开启,关闭"],
        ["appType", "enum", "应用类型", "chat,retrieval,app,query,admin"],
        ["appInfo", "any", "应用其他信息"],
        ["appParent", "string", "父key"]
    ],
    "allowNoneFields": ['appInfo', 'appParent'],
    "hiddenFields": [],
    "indexes": ["appKey"],
    "groupCountFields": [],
    "parents": [],
    "editFields": ["appId", "appUser", "appStatus", "appType", 'appInfo'],
    "tableName": "应用"
}

with open("/tmp/hfwm_tables/app.json", 'w') as f:
    json.dump(app_t, f, ensure_ascii=False)


def load_table_config():
    db_name = local_config()['name']
    if local_config().get('dbName', '') != '':
        db_name = local_config().get('dbName', '')
    table_store = {'cache', 'config', 'data', 'development', 'enums', 'extra', 'perm', 'role', 'setting',
                   'sse', 'template', 'tree', 'messageQueue'}

    table_list = []
    table_dict = {}
    parents_dict = {}
    tables_path1 = search_filepaths('/tmp/hfwm_tables', lambda x: x.endswith('.json'))
    tables_path1.sort()
    tables_path2 = search_filepaths(relative_conf_path('.auto_tables'), lambda x: x.endswith('.json'))
    tables_path2.sort()
    tables_path3 = search_filepaths(relative_conf_path('tables'), lambda x: x.endswith('.json'))
    tables_path3.sort()
    tables_path = tables_path1 + tables_path2 + tables_path3

    for table_path in tables_path:
        table_name = os.path.basename(table_path).replace('.json', '').split('#')[-1]
        if table_name.startswith('tree_'):
            raise Exception(f'{table_name} 不能以 tree_开头')

        if table_name in table_store:
            raise Exception(f'表{table_name} 重复或保留字')

        table_store.add(table_name)

        with open(table_path) as f1:
            table_cfg = json.load(f1)
            if not (isinstance(table_cfg, dict) and 'fields' in table_cfg):
                continue
            table_cfg['tableNameEn'] = table_name
            table_list.append(table_cfg)
            fields = [it[0] for it in table_cfg['fields']]
            for it in fields:
                if '.' in it:
                    raise Exception(f"{it}错误，不能包含.")
            username_key = ''
            for field in table_cfg['fields']:
                if field[1] == 'username':
                    if username_key != '':
                        raise Exception(f"{table_name} usernameKey 重复")
                    username_key = field[0]
                    field[1] = 'string'

            table_dict[table_name] = {
                'fields': fields,
                'fieldsType': {it[0]: it[1] for it in table_cfg['fields']},
                'bindIds': [it[0] for it in table_cfg['fields'] if it[1] == 'id'],
                'parents': table_cfg.get('parents', []),
                'child': [],
                'indexes': table_cfg.get('indexes', []),
                'hiddenFields': table_cfg.get('hiddenFields', []),
                'groupCountFields': table_cfg.get('groupCountFields', []),
                'allowNoneFields': table_cfg.get('allowNoneFields', []),
                'notNoneFields': [field for field in fields if field not in table_cfg.get('allowNoneFields', [])],
                'inheritKeys': table_cfg.get('inheritKeys', []),
                'editFields': table_cfg.get('editFields', []),
                'checks': {it[0]: it[3:] for it in table_cfg['fields']},
                "tableName": table_cfg['tableName'],
                'usernameKey': username_key
            }
            parents_dict[table_name] = table_cfg.get('parents', [])
            check_cfg = table_dict[table_name]
            if len(table_cfg.get('indexes', [])) == 0:
                raise Exception(f'{table_name}缺少索引')
            if table_name != 'auth':

                for it in table_cfg.get('indexes', []):
                    if get_first_word(it) != table_name:
                        log().warning(f'{table_name}不能以{it}作为索引')
                        # raise Exception(f'{table_name}不能以{it}作为索引')

            if len(check_cfg['bindIds']) > 0:
                if not (len(check_cfg['bindIds']) == 1
                        and len(check_cfg['indexes']) == 1
                        and check_cfg['bindIds'][0] == check_cfg['indexes'][0]
                ):
                    raise Exception(f'{table_name}: id类型必须为索引字段且唯一')
            for edit_field in check_cfg['editFields']:
                # if edit_field not in check_cfg['fields'] or get_first_word(edit_field) != table_name or edit_field in \
                #         check_cfg['indexes']:
                #     raise Exception(f'{table_name}不可编辑{edit_field}')
                if edit_field not in check_cfg['fields'] or edit_field in \
                        check_cfg['indexes']:
                    raise Exception(f'{table_name}不可编辑{edit_field}')

    for table_name, cfg in table_dict.items():
        if table_name in ['auth']:
            continue
        duplicates = get_duplicates(cfg['fields'])
        if len(duplicates) > 0:
            raise Exception(f"{table_name}:{duplicates}重复")
        duplicates = get_duplicates(cfg['parents'])
        if len(duplicates) > 0:
            raise Exception(f"{table_name}:{duplicates}重复")

        # continue # 继承自上上级字段无法用下面判断
        parents_name = set()
        for field in cfg['fields']:
            table_name_0 = get_first_word(field)

            if table_name_0 != table_name:
                if table_name_0 in table_dict:
                    if field not in table_dict[table_name_0]['indexes']:
                        raise Exception(f'继承字段{table_name}.{field}为非索引字段')
                    for p_i in table_dict[table_name_0]['indexes']:
                        if p_i not in cfg['fields']:
                            raise Exception(f'组合索引必须完全继承')
                    parents_name.add(table_name_0)
                else:
                    raise Exception(f"错误的字段:{field}")
        if len(cfg['parents']) != len(parents_name):
            raise Exception(f"{table_name} 父表与字段不匹配")
        for it in cfg['parents']:
            if it not in parents_name:
                raise Exception(f"{table_name} 父表与字段不匹配")

    def is_child(child, parent):
        parents = parents_dict[child]
        if parent in parents:
            return True
        # for p1 in parents:
        #     if is_child(p1, parent):
        #         return True
        return False

    table_names = list(table_dict.keys())
    for p_name in table_names:
        for c_name in table_names:
            if is_child(c_name, p_name):
                table_dict[p_name]['child'].append(c_name)

    tree = []
    if os.path.isfile(relative_conf_path('tree.json')):
        with open(relative_conf_path('tree.json')) as f2:
            tree = json.load(f2)
    # for k, v in table_dict.items():
    #     for k1, v1 in v['trees'].items():
    #         if v1 not in tree:
    #             raise Exception(f'{k1}配置无此树')
    return db_name, table_list, table_dict, tree

# 表的规则
# 必须有索引
# 继承必须用索引字段，组合索引必须完全继承
# 字段不能重复
# id类型必须为索引字段且唯一
