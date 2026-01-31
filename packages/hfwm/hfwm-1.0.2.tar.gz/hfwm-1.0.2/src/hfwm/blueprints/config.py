# @Time   : 2023-07-23
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import json
from os import path as op
from flask import Blueprint, jsonify, request
from hfwm.models.common import *

config_bp = Blueprint('config', __name__, url_prefix='/wapi/config')
cfg_files = search_filepaths(relative_conf_path('web_config'), lambda x: x.endswith('.json'))
cfg_dict = {}
for cfg_file in cfg_files:
    with open(cfg_file) as f:
        cfg_dict[op.basename(cfg_file).split('.')[0]] = json.load(f)


@config_bp.route('', methods=['GET'])
def get_config():
    env = request.args.get('env')
    if env is None:
        env = 'production'
    cfg = cfg_dict.get(env)
    assert_condition(cfg is not None, 400, '不存在的配置')
    return jsonify({'code': 0, 'data': cfg, 'msg': ''})


add_no_login('/wapi/config')
