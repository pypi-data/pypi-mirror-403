# @Time   : 2023-05-28
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import os
import json
from redis.exceptions import RedisError
from hfwm.models.common import assert_condition
from hfwm.utils.count1000 import get_counter

exists_dir = set()


def recv_file(data):
    new_count = get_counter()
    t = TimeNow().ymdhmsm_strip()
    info_size = int.from_bytes(data[:2], byteorder='big')
    data_info = json.loads(data[2:info_size + 2])
    data_content = data[info_size + 2:]
    filename = data_info['filename']
    filetype = data_info['filetype']
    dir_name = data_info['dir']
    file_dir = relative_data_path('files', dir_name, t[:8])
    if file_dir not in exists_dir:
        os.makedirs(file_dir, exist_ok=True)
        exists_dir.add(file_dir)
    file_name = f'{filename}_{t}_{new_count:03}.{filetype}'
    file_path = os.path.join(file_dir, file_name)
    with open(file_path, 'wb') as f:
        f.write(data_content)
    return file_path.replace(relative_data_path('files'), '/files')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'webm', 'zip', 'txt', 'md', 'm4a', 'mp3', 'doc',
                      'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'json'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def web_recv_file(files):
    assert_condition('file' in files, 400, 'file字段不存在')
    file = files['file']
    assert_condition(file.filename != '', 400, '请选择文件')
    # log().info(file.filename)
    assert_condition(file and allowed_file(file.filename), 400, "文件格式不正确")
    t = TimeNow().ymdhmsm_strip()
    new_count = get_counter()
    if local_config().get('uploadKeepFilename'):
        file_dir = relative_data_path('files', 'upload', f"{t}_{new_count:03}")
        filename = file.filename
        forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '：', '“', '”']
        for char in forbidden_chars:
            filename = filename.replace(char, '_')
    else:
        file_dir = relative_data_path('files', 'upload')
        filename = f'{t}_{new_count:03}.{file.filename.split(".")[-1]}'

    if file_dir not in exists_dir:
        os.makedirs(file_dir, exist_ok=True)
        exists_dir.add(file_dir)
    file_path = os.path.join(file_dir, filename)
    with open(file_path, 'wb') as f:
        file.save(file_path)
    return file_path.replace(relative_data_path('files'), '/files')
