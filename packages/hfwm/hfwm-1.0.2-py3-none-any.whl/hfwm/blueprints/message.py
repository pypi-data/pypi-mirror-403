# @Time   : 2024-05-15
# @Author : zhangxinhao
# @Compile : True
from flask import Blueprint, jsonify, request
from hfwm.models import message

message_bp = Blueprint('message', __name__, url_prefix='/wapi/message')


@message_bp.route('/send', methods=['POST'])
def send():
    data = request.get_json()
    return jsonify({'code': 0, 'data': message.send_msg(data), 'msg': ''})


@message_bp.route('/find_recv_messages', methods=['POST'])
def find_recv_messages():
    data = request.get_json()
    return jsonify({'code': 0, 'data': message.find_messages(data, 'recv'), 'msg': ''})


@message_bp.route('/find_send_messages', methods=['POST'])
def find_send_messages():
    data = request.get_json()
    return jsonify({'code': 0, 'data': message.find_messages(data, 'send'), 'msg': ''})


@message_bp.route('/find_one_message', methods=['POST'])
def find_one_message():
    data = request.get_json()
    return jsonify({'code': 0, 'data': message.find_one_message(data['id']), 'msg': ''})


@message_bp.route('/process_message', methods=['POST'])
def process_message():
    data = request.get_json()
    return jsonify({'code': 0, 'data': message.process_message(data['groupId']), 'msg': ''})


@message_bp.route('/delete_message', methods=['POST'])
def delete_message():
    data = request.get_json()
    return jsonify({'code': 0, 'data': message.delete_message(data['groupId']), 'msg': ''})
