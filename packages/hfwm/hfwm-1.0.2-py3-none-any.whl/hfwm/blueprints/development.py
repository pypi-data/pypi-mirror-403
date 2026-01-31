# @Time   : 2023-06-23
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import os
from flask import jsonify, Blueprint, render_template_string
from hfwm.models.common import *
from hfwm.models.databases.handle import DataHandle, DT
from hfwm.models.api_doc import doc

table_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Table Page</title>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        summary {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        summary::-webkit-details-marker {
            order: 1;
        }
        summary h3 {
            order: 0;
            margin: 0; /* Remove spacing */
            padding: 0.5em 0; /* Add some padding */
        }
    </style>
</head>
<body>

{% for data in data_all %}
<details>
    <summary>
        <h3>
            {{data["name"]}}
        </h3>
    </summary>

    <table>
        <thead>
        <tr>
            {% for field in data["fields"] %}
            <th>{{field}}</th>
            {% endfor %}
        </tr>
        </thead>
        <tbody>
        {% for row in data["values"] %}
        <tr>
            {% for v in row %}
            <td>{{ v }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
        </tbody>
    </table>
</details>

{% endfor %}

</body>
</html>
'''

development_bp = Blueprint('development', __name__, url_prefix='/wapi/development')


@development_bp.route('/data_clean', methods=['GET'])
def clean():
    DataHandle.clean()
    return jsonify({'code': 0, 'data': None, 'msg': ''})


@development_bp.route('/data_dump', methods=['GET'])
def dump():
    os.system(f'rm -rf {relative_data_path("dump")}')
    os.makedirs(relative_data_path("dump"), exist_ok=True)
    os.system(f'/usr/bin/mongodump  --db {DT.db_name} --out {relative_data_path("dump")}')
    return jsonify({'code': 0, 'data': None, 'msg': ''})


@development_bp.route('/readme', methods=['GET'])
def readme():
    new_table_html = table_html.replace('<title>Table Page</title>', f'<title>{DT.db_name}</title>')
    return render_template_string(new_table_html, data_all=doc)


if local_config().get('openReadme'):
    add_no_login('/wapi/development/readme')
else:
    add_denied_path('/wapi/development/readme')
add_denied_path('/wapi/development/data_clean')
add_denied_path('/wapi/development/data_dump')
