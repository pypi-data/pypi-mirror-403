# @Time   : 2023-05-28
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import traceback
from flask_cors import CORS
from flask import Flask, request, abort, jsonify
from werkzeug.exceptions import HTTPException
from hfwm.utils.save_data import recv_file
from hfwm.models.databases.handle import DataHandle
from hfwm.models.databases.template import DataTemplate as DT


def create_app():
    init_logger("hfwm_backend_" + DT.db_name)
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    @app.before_request
    def before_request():
        if request.path.startswith('/iapi/'):
            log().info(f'{request.remote_addr}:{request.path}')
            request.method == 'POST' and request.path != '/iapi/upload' and log().info(request.get_json())

    @app.route('/iapi/upload', methods=['POST'])
    def upload():
        return jsonify({'code': 0, 'data': recv_file(request.data), 'msg': ''})

    @app.route('/iapi/data/<table_name>/<option>', methods=['POST'])
    def upsert(table_name, option):
        if table_name not in DT.tables:
            abort(404, '表不存在')
        if option not in ['upsert']:
            abort(404, '操作不存在')
        data = request.get_json()
        r = getattr(DataHandle, option)(table_name, data)
        return jsonify({'code': 0, 'data': r, 'msg': ''})

    @app.errorhandler(Exception)
    def error_request(e):
        log().error(traceback.format_exc())
        if isinstance(e, HTTPException):
            return jsonify({'code': 1, 'status': e.code, 'msg': e.description}), e.code
        return jsonify({"code": 1, "msg": str(e)}), 500

    return app
