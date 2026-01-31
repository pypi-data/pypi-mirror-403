# @Time   : 2023-05-28
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import os
import copy
import traceback
from werkzeug.exceptions import HTTPException
from flask import Flask, request, jsonify, Blueprint, render_template, send_file, abort, g
from hfwm.models.common import is_no_login
from hfwm.models.databases.handle import DT
from hfwm.models.auth import Auth
from hfwm.models.app import App
from hfwm.utils import intercept_after_auth
from hfwm.utils.save_data import web_recv_file
from hfwm.blueprints.auth import auth_bp
from hfwm.blueprints.cache import cache_bp
from hfwm.blueprints.config import config_bp
from hfwm.blueprints.data import data_bp
from hfwm.blueprints.development import development_bp
from hfwm.blueprints.enums import enums_bp
from hfwm.blueprints.extra import extra_bp
from hfwm.blueprints.large_uploads import large_uploads_bp
from hfwm.blueprints.message import message_bp
from hfwm.blueprints.perm import perm_bp
from hfwm.blueprints.role import role_bp
from hfwm.blueprints.self_data import self_data_bp
from hfwm.blueprints.setting import setting_bp
from hfwm.blueprints.sse import sse_bp
from hfwm.blueprints.template import template_bp
from hfwm.blueprints.tree import tree_bp
from hfwm.models.make_check import make_check


def create_app():
    init_logger("hfwm_mana_" + local_config()['name'])
    app = Flask(__name__, template_folder=relative_project_path('web'),
                static_url_path='/static', static_folder=relative_project_path('web/static'))
    make_check()

    bp_static1 = Blueprint('app_static', __name__,
                           static_folder=relative_project_path('h5/static'),
                           static_url_path='/app/static')
    app.register_blueprint(bp_static1)
    token_map = []
    try:
        token_map = local_config('token_map.json')
    except:
        pass

    log_conf = {}
    try:
        log_conf = local_config('log.json')
    except:
        pass
    print(log_conf)
    bp_static2 = Blueprint('files', __name__, static_folder=relative_data_path('files'), static_url_path='/files')
    app.register_blueprint(bp_static2)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cache_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(development_bp)
    app.register_blueprint(enums_bp)
    app.register_blueprint(extra_bp)
    app.register_blueprint(large_uploads_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(perm_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(self_data_bp)
    app.register_blueprint(setting_bp)
    app.register_blueprint(sse_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(tree_bp)

    os.makedirs(relative_data_path('files'), exist_ok=True)

    def log_req():
        if request.path in log_conf.get('ignoreRoutes', []):
            return
        real_ip = request.headers.get('X-Real-IP', request.remote_addr)
        if Auth.current() is not None:
            login_info = f'user:{Auth.current().username}'
        else:
            login_info = f'app: {App.current().app_key}'
        if request.method == 'POST' and (
                request.path != '/wapi/upload' and request.path != '/wapi/large_uploads/upload_chunk'):
            data = copy.deepcopy(request.get_json())
            try:
                for k in data.keys():
                    v = data[k]
                    if isinstance(v, str) and (len(v) > 500):
                        data[k] = f"{v[:100]}...(总长{len(v)})"
            except:
                pass
            log_info = f'POST {request.path} {login_info} from:{real_ip} [data]{data}'
        else:
            log_info = f'GET  {request.path} {login_info} from:{real_ip}'
        try:
            log().info(log_info[:1000])
        except:
            pass
    @app.before_request
    def before_request():
        g.auth = None
        g.app = None
        if request.method == 'OPTIONS':
            return 'OK'
        if request.path.startswith('/wapi/'):
            if is_no_login(request.path):
                log().info(request.path)
            else:
                token = request.headers.get('Authorization', '')
                if token:
                    for s1, s2 in token_map:
                        token = token.replace(s1, s2)
                if token.startswith('TK'):
                    Auth.load_by_token(token).set_current()
                    log_req()
                    Auth.current().check_perm_path(request.path)
                elif token.startswith('Bearer '):
                    App.load_by_token(token).set_current()
                    log_req()
                    App.current().check_perm_path(request.path)
                else:
                    abort(401, '认证失败')
            func = intercept_after_auth.get_func(request.path)
            if func is not None:
                r = func()
                if r is not None:
                    return r

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/app/')
    def app_index():
        return send_file(relative_project_path('h5/index.html'))

    @app.route('/wapi/upload', methods=['POST', 'OPTIONS'])
    def upload():
        return jsonify({'code': 0, 'data': web_recv_file(request.files), 'msg': ''})

    @app.route('/favicon.ico', methods=['GET'])
    def get_favicon():
        return ''

    @app.errorhandler(Exception)
    def error_request(e):
        if isinstance(e, HTTPException):
            if e.code == 404:
                log().error('code 404:' + request.path)
            elif e.code == 401:
                log().error(e.description)
            else:
                log().error(traceback.format_exc())
            return jsonify({'code': 1, 'status': e.code, 'msg': e.description}), e.code
        else:
            log().error(traceback.format_exc())
        return jsonify({"code": 1, "msg": str(e)}), 500

    return app
