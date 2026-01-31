# @Time   : 2025-09-25
# @Author : zhangxinhao
# @Compile : True
from hfwm.models.common import *
from hfwm.models.databases.template import DataTemplate as DT


def add_data_perm(table_name, option):
    table_zh = DT.table_dict[table_name]['tableName']
    if option == "查看":
        add_perm(f"数据:{table_zh}:查看", [f'/wapi/data/{table_name}/find_one', f'/wapi/data/{table_name}/find',
                                           f'/wapi/data/{table_name}/count',
                                           f'/wapi/data/{table_name}/group_count',
                                           f'/wapi/data/{table_name}/calculate'])
    elif option == "查看2":
        add_perm(f"数据:{table_zh}:查看", [f'/wapi/data/{table_name}/find_one', f'/wapi/data/{table_name}/find'])
    elif option == "新增":
        add_perm(f"数据:{table_zh}:新增", f'/wapi/data/{table_name}/insert')
    elif option == "更新":
        add_perm(f"数据:{table_zh}:更新", f'/wapi/data/{table_name}/update')
    elif option == "删除":
        add_perm(f"数据:{table_zh}:删除", f'/wapi/data/{table_name}/remove')
    elif option == "更新或新增":
        add_perm(f"数据:{table_zh}:更新或新增", f'/wapi/data/{table_name}/upsert')
