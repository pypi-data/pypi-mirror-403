# @Time   : 2023-06-23
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify, request, abort
from hfwm.models.databases.handle import DT
from hfwm.models.tree import Tree
from hfwm.models.common import *

tree_bp = Blueprint('tree', __name__, url_prefix='/wapi/tree')


@tree_bp.route('/<tree_name>/<option>', methods=['POST'])
def tree_handle(tree_name, option):
    assert_condition(tree_name in DT.tree, 404, tree_name)
    data = request.get_json()
    parent = data.get('parent')
    child = data.get('child')
    r = ''
    if option == 'insert':
        r = Tree.insert(tree_name, parent, child)
    elif option == 'insert_multilevel':
        r = Tree.insert_multilevel(tree_name, parent)
    elif option == 'find':
        r = Tree.find(tree_name, parent)
    elif option == 'remove':
        r = Tree.remove(tree_name, parent)
    else:
        abort(404, option)
    return jsonify({'code': 0, 'data': r, 'msg': ''})


