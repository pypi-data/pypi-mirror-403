# @Time   : 2023-07-27
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify
from hfwm.models.common import *

perm_bp = Blueprint('perm', __name__, url_prefix='/wapi/perm')


@perm_bp.route('/list')
def get_perms():
    return jsonify({'code': 0, 'data': get_perm_names(), 'msg': ''})
