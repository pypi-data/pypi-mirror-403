# @Time   : 2023-05-26
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import os
import copy
from bson.objectid import ObjectId
from pymongo import MongoClient
from typing import Dict

from hfwm.models.databases.template import DataTemplate as DT, assert_condition
from hfwm.models.make_charts import draw_histogram, draw_pie

try:
    from pymongo.collection import Collection
except:
    from pymongo.synchronous.collection import Collection

_instance = MongoClient(os.getenv('MONGO_CONNECT', "mongodb://localhost:27017"))
_instance.list_database_names()


def init_db():
    db = _instance[DT.db_name]
    mongo_table_dict = {}
    for tree_name in DT.tree:
        mongo_table_dict['tree_' + tree_name] = db['tree_' + tree_name]
        mongo_table_dict['tree_' + tree_name].create_index("child", unique=True)
    for table_name in DT.tables:
        mongo_table_dict[table_name] = db[table_name]
        indexes = DT.table_dict[table_name]['indexes']
        if len(indexes) > 0:
            mongo_table_dict[table_name].create_index([(key, 1) for key in indexes], unique=True)
        for group_count_field in DT.table_dict[table_name]['groupCountFields']:
            mongo_table_dict[table_name].create_index(group_count_field)

    mongo_table_dict['super_admin'] = db['super_admin']
    mongo_table_dict['super_admin'].create_index('username', unique=True)

    mongo_table_dict['auth'] = db['auth']
    mongo_table_dict['auth'].create_index('username', unique=True)

    mongo_table_dict['role'] = db['role']
    mongo_table_dict['role'].create_index('role', unique=True)
    mongo_table_dict['cache'] = db['cache']
    mongo_table_dict['cache'].create_index('username', unique=True)

    mongo_table_dict['setting'] = db['setting']
    mongo_table_dict['setting'].create_index('name', unique=True)

    mongo_table_dict['messageQueue'] = db['messageQueue']
    mongo_table_dict['messageQueue'].create_index('sendUser')
    mongo_table_dict['messageQueue'].create_index('targetUser')
    mongo_table_dict['messageQueue'].create_index('channel')
    mongo_table_dict['messageQueue'].create_index('groupId')

    return mongo_table_dict


class DataHandle:
    _table_dict: Dict[str, Collection] = init_db()

    @classmethod
    def get_table(cls, table_name):
        r = cls._table_dict.get(table_name)
        assert_condition(r is not None, 400, f"表{table_name}不存在")
        return r

    @classmethod
    def _get_parents_data(cls, table_name, data):
        all_parent_info = {}
        for parent in DT.table_dict[table_name]['parents']:
            indexes = DT.table_dict[parent]['indexes']
            if all(data.get(field) is not None for field in indexes):
                parent_p_query = {key: data[key] for key in indexes}
                p_info = cls.get_table(parent).find_one(parent_p_query)
                if p_info is not None:
                    all_parent_info.update(p_info)
        if '_id' in all_parent_info:
            all_parent_info.pop('_id')
        return all_parent_info

    @classmethod
    def _collect_inherit(cls, table_name, parents_data):
        inherit_keys = DT.table_dict[table_name]['inheritKeys']
        p_info = {}
        for inherit_key in inherit_keys:
            if inherit_key in parents_data:
                p_info[inherit_key] = parents_data[inherit_key]
        return p_info

    @classmethod
    def find_one(cls, table_name, data, hide=True, data_is_query=True):
        table = cls.get_table(table_name)
        if data_is_query:
            if data.get('id') is not None:
                query = {'_id': ObjectId(data['id'])}
            else:
                query, _ = DT.data_format(table_name, data)
            cur_docu = table.find_one(query)
        else:
            try:
                cur_docu = data
                query, _ = DT.data_format(table_name, data)
            except:
                cur_docu = None
                table.delete_one({'_id': data['_id']})
                log().error(f"格式校验错误, 删除{table_name}: {data}")

        if cur_docu is None:
            return None

        cur_id = cur_docu['_id']

        if hide:
            cur_docu = {k: v for k, v in cur_docu.items() if k not in DT.table_dict[table_name]['hiddenFields']}

        cur_docu_copy = copy.deepcopy(cur_docu)
        for parent in DT.table_dict[table_name]['parents']:
            p_query = {key: cur_docu[key] for key in DT.table_dict[parent]['indexes']}
            parent_data = cls.find_one(parent, p_query, hide, True)
            if parent_data is not None:
                cur_docu_copy.update(parent_data)
        inherit_data = cls._collect_inherit(table_name, cur_docu_copy)
        correct_flag = False
        for k, v in inherit_data.items():
            if k not in cur_docu or cur_docu[k] != v:
                correct_flag = True
                break
        if correct_flag:
            cur_docu.update(inherit_data)
            # print(f'{table_name}.update_one', query, cur_docu)
            table.update_one(query, {'$set': cur_docu}, upsert=False)
        r_cur_docu_copy = {'id': str(cur_id)}
        cur_docu_copy.pop('_id')
        if 'id' in cur_docu_copy:
            cur_docu_copy.pop('id')
        if '_id' in cur_docu_copy:
            cur_docu_copy.pop('_id')
        r_cur_docu_copy.update(dict(sorted(cur_docu_copy.items())))
        return r_cur_docu_copy

    @classmethod
    def find(cls, table_name, data, hide=True):
        table = cls.get_table(table_name)
        sort_key = data.get('sortKey')
        sort_key = '_id' if sort_key is None else str(sort_key)
        sort_reverse = 1 if str(data.get('sortReverse')) == '1' else -1
        page_num = int(data['pageNum']) - 1
        assert_condition(page_num >= 0, 400, "页面编号需为非负数")
        page_size = int(data['pageSize'])
        assert_condition(0 < page_size <= 500, 400, "page_size 取值范围是1-500")
        new_query = DT.make_query(table_name, data)
        total_num = table.count_documents(new_query)
        items = table.find(new_query).sort(sort_key, sort_reverse).skip(page_num * page_size).limit(page_size)
        records = list()
        for it in items:
            x = cls.find_one(table_name, it, hide, False)
            if x is not None:
                records.append(x)
        return {"totalNum": total_num, "records": records}

    @classmethod
    def count(cls, table_name, data):
        table = cls.get_table(table_name)
        new_query = DT.make_query(table_name, data)
        total_num = table.count_documents(new_query)
        return total_num

    @classmethod
    def calculate(cls, table_name, data):
        table = cls.get_table(table_name)
        field = str(data.get('field'))
        assert_condition(DT.table_dict[table_name]['fieldsType'][field] in ['float', 'int'], 400,
                         f'{table_name}.{field}不能计算指标')
        opts_dict = {"count": {"$sum": 1},
                     "ave": {"$avg": f"${field}"},
                     "sum": {"$sum": f"${field}"},
                     "max": {"$max": f"${field}"},
                     "min": {"$min": f"${field}"}}
        opts = data.get('opts', [])
        if len(opts) == 0:
            opts = ['count', 'ave', 'sum', 'max', 'min']
        group_v = {"_id": None}
        for opt in opts:
            assert_condition(opt in opts_dict, 400, f'错误的opt:{opt}')
            group_v[opt] = opts_dict[opt]

        pipeline = [
            {"$match": DT.make_query(table_name, data.get('query'))},
            {"$group": group_v}
        ]
        result = list(table.aggregate(pipeline))
        r = {
            'status': 0,
            "count": 0,
            "ave": 0,
            "sum": 0,
            "max": 0,
            "min": 0,
        }
        if len(result) == 0:
            return r
        r['status'] = 1
        r.update(result[0])
        r.pop('_id')
        return r

    @classmethod
    def group_count(cls, table_name, data):
        table = cls.get_table(table_name)
        field = str(data.get('field'))
        sum_field = data.get('sumField')
        assert_condition(field in DT.table_dict[table_name]['groupCountFields'], 400,
                         f'{table_name}.{field}不能做统计')
        limit = int(data['limit'])
        assert_condition(0 < limit <= 200, 500, "0 < limit <= 200")
        pipeline = []
        if data.get("query") is not None:
            pipeline.append({"$match": DT.make_query(table_name, data.get('query'))})
        sum_what = 1
        if sum_field:
            sum_what = "$" + str(sum_field).strip()
        pipeline.extend([
            {"$group": {"_id": "$" + str(field).strip(), "count": {"$sum": sum_what}}},
            {"$sort": {"count": -1}},
            {"$limit": limit + 1}
        ])
        if sum_what == 1:
            total = table.count_documents(DT.make_query(table_name, data.get('query')))
        else:
            pipelinex = [
                {"$match": DT.make_query(table_name, data.get('query'))},
                {"$group": {"_id": None, "sum": {"$sum": sum_what}}}
            ]
            total = list(table.aggregate(pipelinex))[0]['sum']

        result = list(table.aggregate(pipeline))
        other = 0
        if len(result) == limit + 1:
            other = total
            for i in range(limit):
                other -= result[i]['count']
        r = []
        for i in range(min(limit, len(result))):
            r.append({
                'key': result[i]['_id'],
                'count': result[i]['count']
            })
        f_r = {'totalNum': total, 'counts': r, 'other': other}
        if data.get('chart', '') == 'pie':
            chart_path = draw_pie(copy.deepcopy(f_r))
            f_r['chart'] = chart_path
        elif data.get('chart', '') == 'histogram':
            chart_path = draw_histogram(copy.deepcopy(f_r))
            f_r['chart'] = chart_path
        return f_r

    @classmethod
    def update(cls, table_name, data_o, check_allow_edit=True, update_time=True):
        # 先获取旧数据，转成一样的
        table = cls.get_table(table_name)
        data = {}
        # todo 这里的问题是id已经失效了，data里不可能有id
        for k, v in data_o.items():
            if k in ['_id', 'id']:
                continue
            r, v = DT.convert_value(table_name, k, v)
            if r:
                data[k] = v

        if 'id' in data:
            old_data = table.find_one({'_id': ObjectId(data['id'])})
        else:
            p_query, _ = DT.data_format(table_name, data)
            old_data = table.find_one(p_query)
        assert_condition(old_data is not None, f'无法找到更新源')
        new_data = copy.deepcopy(old_data)
        if 'id' in data:
            data.pop('id')
        if check_allow_edit:
            data_keys = list(data.keys())
            for key in data_keys:
                if key not in DT.table_dict[table_name]['indexes'] \
                        and key not in DT.table_dict[table_name]['editFields']:
                    data.pop(key)
        new_data.update(data)
        for index_key in DT.table_dict[table_name]['indexes']:
            assert_condition(old_data[index_key] == new_data[index_key], 400, f"无法更新{index_key}")

        parents_data = cls._get_parents_data(table_name, data)
        inherit_info = cls._collect_inherit(table_name, parents_data)
        new_data.update(inherit_info)

        # 即使数据相同，时间要更新
        p_query, _ = DT.data_format(table_name, new_data)
        if update_time:
            new_data[f'{table_name}UpdateTime'] = TimeNow().ymdhms()
        # print(f'{table_name}.update_one', p_query, new_data)
        r = table.update_one(p_query, {'$set': new_data}, upsert=False)
        if r.modified_count == 0:
            return 0

        diff_dict = {}
        for k, v in new_data.items():
            if k not in old_data or old_data[k] != v:
                diff_dict[k] = v
        for child_table_name in DT.table_dict[table_name]['child']:
            update_data = cls._collect_inherit(child_table_name, diff_dict)
            if len(update_data) == 0:
                continue
            p_query = {key: new_data[key] for key in DT.table_dict[table_name]['indexes']}
            child_table = cls.get_table(child_table_name)
            if len(DT.table_dict[child_table_name]['child']) == 0:
                # print(f'{table_name} {child_table_name}.update_many', p_query, update_data)
                child_table.update_many(p_query, {'$set': update_data}, upsert=False)
                continue
            child_docu = child_table.find(p_query)
            for docu in child_docu:
                docu.pop('_id')
                docu.update(update_data)
                cls.update(child_table_name, docu, False, False)

        return r.modified_count

    @classmethod
    def insert(cls, table_name, data, parents_data_o=None):
        oid = ObjectId()
        if len(DT.table_dict[table_name]['bindIds']) == 1:
            data[DT.table_dict[table_name]['bindIds'][0]] = str(oid)
        p_query, data = DT.data_format(table_name, data)
        DT.check_insert(table_name, data)
        if parents_data_o is not None:
            parents_data = parents_data_o
        else:
            parents_data = cls._get_parents_data(table_name, data)
        # parents_data = cls._get_parents_data(table_name, data)
        inherit_info = cls._collect_inherit(table_name, parents_data)
        # 新增的数据与父表隔离，所以相互更新是可以的
        data.update(inherit_info)
        data = {key: value for key, value in data.items() if key not in ['id', '_id']}
        ymdhms = TimeNow().ymdhms()
        data[f'{table_name}CreateTime'] = ymdhms
        data[f'{table_name}UpdateTime'] = ymdhms
        table = cls.get_table(table_name)
        data['_id'] = oid
        inserted_id = str(table.insert_one(data).inserted_id)
        return str(inserted_id)

    @classmethod
    def upsert(cls, table_name, data):
        p_query, data = DT.data_format(table_name, data)
        if cls.get_table(table_name).find_one(p_query):
            return {'type': "update", 'data': cls.update(table_name, data)}
        return {'type': "insert", 'data': cls.insert(table_name, data)}

    @classmethod
    def distinct(cls, table_name, data):
        table = cls.get_table(table_name)
        field = str(data.get('field'))
        assert_condition(field in DT.table_dict[table_name]['groupCountFields'], 400, f'{table_name}.{field}不能做统计')
        return list(table.distinct(field))

    @classmethod
    def get_enums(cls, table_name, data):
        field = str(data.get('field'))
        table_info = DT.table_dict.get(table_name)
        assert_condition('enum' in table_info['fieldsType'].get(field, ''), 400, f'字段{field}不是枚举类型')
        r = table_info['checks'].get(field)
        assert_condition(r is not None, 400, f"{table_name}.{field} 不是枚举字段")
        return r[0].split(',')

    @classmethod
    def remove(cls, table_name, data):
        table = cls.get_table(table_name)
        if data.get('id') is not None:
            query = {'_id': ObjectId(data['id'])}
        else:
            query, _ = DT.data_format(table_name, data)
        return table.delete_one(query).deleted_count

    @classmethod
    def clean(cls):
        _instance.drop_database(DT.db_name)
        init_db()
