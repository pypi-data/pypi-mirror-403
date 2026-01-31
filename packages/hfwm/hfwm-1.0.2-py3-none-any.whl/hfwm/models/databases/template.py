# @Time   : 2023-06-02
# @Author : zhangxinhao
# @Compile : True
import re
from bson.objectid import ObjectId
from pymongo import MongoClient
from hfwm.models.databases.template_load import load_table_config
from hfwm.models.common import assert_condition
from hfwm.models.check import get_checker


def convert_value_one(field_type, value):
    if field_type in ['int', 'list_int']:
        try:
            return int(value)
        except ValueError:
            assert_condition(False, 400, f'{value}不是整数')

    if field_type in ['float', 'list_float']:
        try:
            return float(value)
        except ValueError:
            assert_condition(False, 400, f'{value}不是浮点数')

    if field_type in ['id', 'enum', 'tree', 'string', 'list_enum', 'list_tree', 'list_string']:
        return str(value)
    if field_type == 'any':
        return value
    assert_condition(False, 400, f"错误的模板配置类型:{field_type}")


class DataTemplate:
    db_name, table_list, table_dict, tree = load_table_config()
    tables = list(table_dict.keys())
    check_convert = {}

    @classmethod
    def convert_value(cls, table_name, field, value):
        if '.' in field:
            field = field.split('.')[0]

        if field == '_id':
            return True, ObjectId(value)

        if 'CreateTime' in field:
            return True, value.strip()

        if 'UpdateTime' in field:
            return True, value.strip()

        if field.endswith('OtherInfo'):
            return True, value

        if field.endswith('BuiltinId'):
            return True, value.strip()

        # auth表不转换
        if field in ['username', 'nickname', 'roles']:
            return True, value

        table = cls.table_dict.get(table_name)
        if table is None:
            return False, None

        if field in table['inheritKeys']:
            return cls.convert_value(cls.get_table_name(field), field, value)

        field_type = table['fieldsType'].get(field)
        # 多余字段丢弃
        if field_type is None:
            return False, None

        if value is None:
            if field in table['allowNoneFields']:
                return True, None
            return False, None

        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, list) and (len(value) > 0) and isinstance(value[0], str):
            value = [it.strip() for it in value]

        func = get_checker(field)
        if field_type.startswith('list'):
            assert_condition(isinstance(value, list), 400, f"错误的值:{field}")
            return True, [func(convert_value_one(field_type, it)) for it in value]
        else:
            return True, func(convert_value_one(field_type, value))

    @classmethod
    def get_table_name(cls, key):
        if key == '_id':
            return 'table exist'
        if key in ['username', 'nickname', 'roles']:
            return 'auth'
        for table_name in cls.tables:
            if len(key) > len(table_name):
                if key.startswith(table_name):
                    if key[len(table_name)].isupper():
                        return table_name
        return None

    @classmethod
    def check_query_field_type(cls, key, value):
        if value is None:
            return
        assert_condition(isinstance(value, str) or isinstance(value, int) or isinstance(value, float),
                         400, f"{key}错误")

    @classmethod
    def make_query(cls, table_name, query):
        if query is None:
            return {}
        new_query = {}
        for key, value in query.get('equalCondition', {}).items():
            if (value is not None) and (value != '') and (table_name is not None):
                if value == 'EISNULL:NONNULL':
                    new_query[key] = {"$exists": True, "$nin": [None, "", [], {}]}
                elif value == 'EISNULL:NULL':
                    or1 = [
                        {key: {"$exists": False}},
                        {key: {"$in": [None, "", [], {}]}}
                    ]
                    new_query.setdefault('$and', []).append({"$or": or1})
                else:
                    r, value = cls.convert_value(table_name, key, value)
                    if r:
                        cls.check_query_field_type(key, value)
                        new_query[key] = value
        for key, value in query.get('containCondition', {}).items():
            if (value is not None) and (table_name is not None):
                r, value = cls.convert_value(table_name, key, value)
                if r:
                    cls.check_query_field_type(key, value)
                    new_query[key] = {"$regex": re.escape(value)}

        for keys, value in query.get('multiContainCondition', {}).items():
            if value is None:
                continue
            value = str(value).replace(':', '').replace('{', '').replace('}', '').replace(' ', '')
            if len(value) == 0:
                continue
            keys = keys.split(',')
            or2 = []
            for key in keys:
                if table_name is None:
                    continue
                or2.append({key: {"$regex": value}})
            if len(or2) > 0:
                new_query.setdefault('$and', []).append({"$or": or2})

        for key, values in query.get('rangeCondition', {}).items():
            if isinstance(values, list) and (len(values) == 2) and (table_name is not None):
                if values[0] is not None:
                    r, value = cls.convert_value(table_name, key, values[0])
                    if r:
                        cls.check_query_field_type(key, value)
                        new_query.setdefault(key, {})
                        new_query[key]['$gte'] = value
                if values[1] is not None:
                    r, value = cls.convert_value(table_name, key, values[1])
                    if r:
                        cls.check_query_field_type(key, value)
                        new_query.setdefault(key, {})
                        new_query[key]['$lte'] = value

        for key, values in query.get('inCondition', {}).items():
            if isinstance(values, list) and (table_name is not None):
                new_query.setdefault(key, {})
                new_query[key]['$in'] = []
                for v in values:
                    # todo list_string之前出错了
                    # r, value = cls.convert_value(table_name, key, v)
                    # if r:
                    #     new_query[key]['$in'].append(value)
                    cls.check_query_field_type(key, v)
                    new_query[key]['$in'].append(v)

        for key in query.get('existArray', []):
            assert_condition(isinstance(key, str), 400, 'existArray格式错误')
            if not key.startswith('~'):
                new_query.setdefault("$and", [])
                and1 = [{key: {"$exists": True}}, {key: {"$not": {"$size": 0}}}]
                new_query.setdefault('$and', []).append({"$and": and1})
            else:
                key = key.replace('~', '')
                new_query.setdefault("$or", [])
                or3 = [{key: {"$exists": False}}, {key: {"$size": 0}}]
                new_query.setdefault('$and', []).append({"$or": or3})
        return new_query

    @classmethod
    def data_format(cls, table_name, data):
        assert_condition(cls.table_dict.get(table_name) is not None, 400, f"表{table_name}不存在")
        new_data = {}
        for k, v in data.items():
            if k == '_id':
                continue
            r, v = cls.convert_value(table_name, k, v)
            if r:
                new_data[k] = v
        indexes = cls.table_dict[table_name]["indexes"]
        p_query = {key: new_data[key] for key in indexes if new_data[key] is not None}
        assert_condition(len(p_query) == len(indexes), 400, "索引字段不能为空")
        return p_query, new_data

    @classmethod
    def check_insert(cls, table_name, data):
        table = cls.table_dict.get(table_name)
        assert_condition(table is not None, 400, f'表{table_name}不存在')
        for field in table['notNoneFields']:
            if field not in data:
                raise Exception(f"{table_name}缺少{field}")

    @classmethod
    def get_username_key(cls, table_name):
        table = cls.table_dict.get(table_name)
        assert_condition(table is not None, 400, f'表{table_name}不存在')
        return table.get('usernameKey', '')
