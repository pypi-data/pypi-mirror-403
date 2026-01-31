# @Time   : 2023-09-20
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import get_class_or_func
from hfwm.models.databases.template import DataTemplate as DT
from hfwm.models.tree import Tree
from hfwm.models.check import add_checker
from hfwm.models.common import assert_condition


def enum_checker(field, value, enum_values):
    assert_condition(value in enum_values, 400, f"{field}错误的取值{value},允许的值:{enum_values}")


def tree_checker(field, value, tree_name):
    assert_condition(Tree.get_table(tree_name).find_one({'child': value}) is not None, 400, f"{field}错误的取值{value},tree:{tree_name}")


def make_check():
    for table_cfg in DT.table_dict.values():
        for k, t in table_cfg['fieldsType'].items():
            if 'enum' in t:
                if len(table_cfg['checks'][k]) == 0:
                    raise Exception(f'{k}未配置枚举值')
                else:
                    enum_values = table_cfg['checks'][k][0].split(',')
                    add_checker(k, enum_checker, enum_values)
            elif 'tree' in t:
                if len(table_cfg['checks'][k]) == 0:
                    raise Exception(f'{k}未配置')
                tree_name = table_cfg['checks'][k][0]
                if tree_name not in DT.tree:
                    raise Exception(f"树{tree_name}不存在")

                add_checker(k, tree_checker, tree_name)
            elif len(table_cfg['checks'][k]) > 0:
                func_path = table_cfg['checks'][k][0]
                func_args = table_cfg['checks'][k][1:]
                func = get_class_or_func(func_path)
                add_checker(k, func, *func_args)
