# @Time   : 2024-09-12
# @Author : zhangxinhao
# @Compile : True
from hfwm.models.databases.handle import DT
auto_pages = []
for table in DT.table_list:
    if table['tableNameEn'] in ['auth', 'oplog', 'autopage']:
        continue
    r = {
        "tableNameEn": table['tableNameEn'],
        "tableName": table['tableName'],
        "fields": [],
        "perms": table.get('autoPagePerms', 'r')

    }
    for field in table['fields']:
        if not field[0] in table.get('hiddenFields'):
            r['fields'].append({
                'key': field[0],
                'type': field[1],
                'name': field[2],
                'value': None if 'enum' not in field[1] else field[3].split(',')
            })
    auto_pages.append(r)
