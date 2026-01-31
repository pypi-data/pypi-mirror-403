# @Time   : 2023-06-02
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import os
import json
from hfwm.models.databases.template import DataTemplate as DT

doc = []

for i, table in enumerate(DT.table_list):
    values = []
    name = f"表{i + 1}: {table['tableNameEn']}({table['tableName']})"
    if len(table['parents']) != 0:
        name += f"，父表：{','.join(table['parents'])}"
    data = {
        "name": name,
        "fields": ["字段", "含义", "类型", "是否可为空", "是否为敏感数据", "是否为索引", "是否能按该字段统计",
                   "是否可编辑"],
        "values": values
    }
    username_key = DT.get_username_key(table['tableNameEn'])
    for field_info in table['fields']:
        row = [field_info[0], field_info[2], field_info[1] if username_key != field_info[0] else 'username',
               field_info[0] in table.get('allowNoneFields', []),
               field_info[0] in table.get('hiddenFields', []),
               field_info[0] in table.get('indexes', []),
               field_info[0] in table.get('groupCountFields', []),
               field_info[0] in table.get('editFields', [])]
        values.append(row)
    doc.append(data)
