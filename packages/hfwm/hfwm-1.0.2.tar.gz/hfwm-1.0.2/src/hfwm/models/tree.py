# @Time   : 2023-05-26
# @Author : zhangxinhao
# @Compile : True
import re
from hfwm.models.databases.handle import DataHandle
from hfwm.models.common import assert_condition


class Tree:

    @classmethod
    def get_table(cls, table_name):
        return DataHandle.get_table('tree_' + table_name)

    @classmethod
    def insert(cls, tree_name, parent, child):
        assert_condition(parent.startswith("##") and parent.endswith('#'), 400, f"parent:{parent}格式错误")
        assert_condition('#' not in child, 400, f"child:{child}格式错误")
        table = cls.get_table(tree_name)
        if parent != '##':
            assert_condition(table.find_one({'child': parent}) is not None, 400, f"parent:{parent} 不存在该父节点")
        real_child = parent + child + '#'
        if table.find_one({'parent': parent, 'child': real_child}) is not None:
            return 0
        if table.find_one({'order': -1}) is not None:
            table.update_many({}, {"$inc": {"order": 1}})
        r = table.update_one({'parent': parent, 'child': real_child},
                             {'$setOnInsert': {'parent': parent, 'child': real_child, 'order': -1}},
                             upsert=True).modified_count
        assert_condition(r is not None, 400, '添加失败')
        if r:
            table.update_many({}, {"$inc": {"order": 1}})
        return r

    @classmethod
    def find(cls, tree_name, parent):
        assert_condition(parent.startswith("##") and parent.endswith('#'), 400, f"parent:{parent}格式错误")
        table = cls.get_table(tree_name)
        items = table.find({'parent': parent}).sort('order', 1)
        r = []
        for it in items:
            r.append(it['child'].split('#')[-2])
        return r

    @classmethod
    def update(cls, tree_name, parent, child, new_child):
        assert_condition(parent.startswith("##") and parent.endswith('#'), 400, f"parent:{parent}格式错误")
        assert_condition('#' not in child, 400, f"child:{child}格式错误")
        assert_condition('#' not in new_child, 400, f"new_child:{new_child}格式错误")

        table = cls.get_table(tree_name)
        if parent != '##':
            assert_condition(table.find_one({'child': parent}) is not None, 400, f"parent:{parent} 不存在该父节点")
        real_child = parent + child + '#'
        real_child_new = parent + new_child + '#'
        return table.update_one({'parent': parent, 'child': real_child},
                                {'$set': {'parent': parent, 'child': real_child_new}}, upsert=False).modified_count

    @classmethod
    def move(cls, tree_name, parent, child, target_child):
        # 插入之前
        assert_condition(parent.startswith("##") and parent.endswith('#'), 400, f"parent:{parent}格式错误")
        assert_condition('#' not in child, 400, f"child:{child}格式错误")
        assert_condition('#' not in target_child, 400, f"new_child:{target_child}格式错误")
        target_child = target_child.replace(':', '').replace('{', '')
        table = cls.get_table(tree_name)
        if parent != '##':
            assert_condition(table.find_one({'child': parent}) is not None, 400, f"parent:{parent} 不存在该父节点")
        real_child = parent + child + '#'

        real_child_target = parent + target_child + '#'
        order = 0
        t = table.find_one({'child': real_child_target})
        if t is None:
            t = table.find_one({'parent': parent}, sort=[("order", -1)])
            if t is not None:
                order = t['order'] + 1
        else:
            order = t['order']
        print(order)

        table.update_many({'parent': parent, "order": {"$gte": order}}, {"$inc": {"order": 1}})
        print(list(table.find()))

        return table.update_one({'child': real_child}, {'$set': {'order': order}}, upsert=False).modified_count

    @classmethod
    def remove(cls, tree_name, parent):
        assert_condition(parent.startswith("##") and parent.endswith('#'), 400, f"parent:{parent}格式错误")
        table = cls.get_table(tree_name)
        r = 0
        r += table.delete_many({'parent': {"$regex": re.escape(parent)}}).deleted_count
        r += table.delete_many({'child': parent}).deleted_count
        return r

    @classmethod
    def insert_multilevel(cls, tree_name, full_name):
        assert_condition(full_name.startswith("##") and full_name.endswith('#'), 400, f"full_name:{full_name}格式错误")
        if cls.get_table(tree_name).find_one({'child': full_name}) is not None:
            return
        full_name = full_name[2:-1]
        childs = full_name.split('#')
        r = 0
        for i in range(len(childs)):
            parent = '##' + '#'.join(childs[:i]) + '#'
            if parent == '###':
                parent = '##'
            child = childs[i]
            r += cls.insert(tree_name, parent, child)
        return r

    @staticmethod
    def split_child(child):
        qs = child.strip('#').split('#')
        r = ['##']
        for q in qs:
            r.append(r[-1] + q + '#')
        return r[1:]
