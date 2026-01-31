# @Time   : 2023-09-28
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify
from hfwm.models.template import get_template, get_templates

template_bp = Blueprint('template', __name__, url_prefix='/wapi/template')


@template_bp.route('/<template_dir>', methods=['GET'])
def wapi_templates(template_dir):
    return jsonify({'code': 0, 'data': get_templates(template_dir), 'msg': ''})


@template_bp.route('/<template_dir>/<template>', methods=['GET'])
def wapi_template(template_dir, template):
    return jsonify({'code': 0, 'data': get_template(template_dir, template), 'msg': ''})
