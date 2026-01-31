# @Time   : 2023-07-11
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import TimeNow
from flask import Blueprint, jsonify, request
from hfwm.models.auto_page import auto_pages
from hfwm.models.common import assert_condition
from hfwm.models.databases.handle import DataHandle, DT
from hfwm.models.auth import Auth

extra_bp = Blueprint('extra', __name__, url_prefix='/wapi/extra')


@extra_bp.route('/auto_pages', methods=['GET'])
def auto_pages_func():
    return jsonify({'code': 0, 'data': auto_pages, 'msg': ''})


auto_pages_dict = {}


def make_auto_pages_dict():
    for auto_page in auto_pages:
        fields_dict = {}
        for field in auto_page['fields']:
            fields_dict[field['key']] = field
        auto_pages_dict[auto_page['tableNameEn']] = {
            'tableNameEn': auto_page['tableNameEn'],
            'tableName': auto_page['tableName'],
            'fields': fields_dict,
            "perms": auto_page['perms']
        }


make_auto_pages_dict()


def get_input_type(field_config):
    input_type = 'input'
    if 'string' in field_config['type']:
        if field_config['name'].endswith('-time'):
            input_type = 'date'
        if field_config['name'].endswith('-image'):
            input_type = 'img'
    if 'enum' in field_config['type']:
        input_type = 'select'
    return input_type


@extra_bp.route('/auto_pages/ai/1', methods=['POST'])
def auto_pages_ai_1():
    data = request.get_json()
    table_name = data['tableName']
    show_fields = data.get('showFields', [])
    if show_fields is None:
        show_fields = []
    query_fields = data.get('queryFields', [])
    if query_fields is None:
        query_fields = []
    assert_condition(table_name in auto_pages_dict, 400, "该表名不存在")
    fields_dict = auto_pages_dict[table_name]['fields']
    page_name = auto_pages_dict[table_name]['tableName'] + '-' + TimeNow().ymdhms_strip()
    show_config = []
    for field in show_fields:
        assert_condition(field in fields_dict, 400, f"字段{field}不存在")
        field_config = fields_dict[field]
        # page_name = page_name + '_' + field_config['name'].split('-')[0]
        show_config.append({
            "label": field_config['name'],
            "key": field_config['key'],
            "showType": field_config['type'],
            "inputType": get_input_type(field_config)
        })
    assert_condition(len(show_config) > 0, 400, "展示字段必填")

    query_config = []
    for field in query_fields:
        assert_condition(field in fields_dict, 400, f"字段{field}不存在")
        field_config = fields_dict[field]
        match_type = {
                'input': 'Contain',
                'select': 'Equal',
                'date': 'Range',
                'img': 'Contain'
            }[get_input_type(field_config)]
        if field_config['type'] in ['int', 'float']:
            match_type = 'Equal'
        query_config.append({
            "label": field_config['name'],
            "key": field_config['key'],
            "showType": field_config['type'],
            "inputType": get_input_type(field_config),
            "match": match_type
        })

    r = DataHandle.insert('autopage', {
        "autopageUser": Auth.current().username,
        "autopageName": page_name,
        "autopageConfig": {
            "name": table_name,
            "perms": auto_pages_dict[table_name]['perms'],
            "table": show_config,
            "search": query_config
        }
    })
    return jsonify({'code': 0, 'data': r, 'msg': ''})


@extra_bp.route('/auto_pages/template/<table_name>', methods=['GET'])
def get_template(table_name, _no_use=None):
    for table in DT.table_list:
        if table['tableNameEn'] == table_name:
            return jsonify({'code': 0, 'data': table, 'msg': ''})
    return jsonify({'code': 0, 'data': None, 'msg': ''})


