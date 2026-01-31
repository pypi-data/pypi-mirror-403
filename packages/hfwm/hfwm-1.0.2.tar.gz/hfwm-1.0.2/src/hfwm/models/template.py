# @Time   : 2023-09-28
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import json
import copy
from hfwm.models.common import assert_condition

templates_dir = relative_conf_path('templates')
templates_dict = {}

json_paths = search_filepaths(templates_dir, lambda x: x.endswith('.json'))
for json_path in json_paths:
    splits = json_path[len(templates_dir) + 1:].split('/')
    if len(splits) != 2:
        continue
    with open(json_path, 'r') as f:
        info = json.load(f)
    template_dir_, json_name = splits
    json_index, json_name = json_name.replace('.json', '').split('#')
    templates_dict.setdefault(template_dir_, {})
    templates_dict[template_dir_][json_name] = {"templateName":json_name, "showIndex":json_index, "data":info}


def get_templates(template_dir):
    assert_condition(template_dir in templates_dict, 400, f'模板类型{template_dir}不存在')
    r = []
    for _, v in templates_dict[template_dir].items():
        r.append(copy.deepcopy(v))
    r.sort(key=lambda x: x['showIndex'], reverse=False)

    return r


def get_template(template_dir, template):
    assert_condition(template_dir in templates_dict, 400, f'模板类型{template_dir}不存在')
    assert_condition(template in templates_dict[template_dir], 400, f'模板类型{template_dir}.{template}不存在')
    r = copy.deepcopy(templates_dict[template_dir][template])
    return r
