# @Time   : 2025-04-10
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import relative_data_path
import os
import json
import shutil
import hashlib
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

large_uploads_bp = Blueprint('large_uploads', __name__, url_prefix='/wapi/large_uploads')
UPLOAD_FOLDER = relative_data_path('large_uploads', 'uploads')
TEMP_FOLDER = relative_data_path('large_uploads', 'temp')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)


def calculate_file_md5(file_path):
    """计算文件MD5"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()

@large_uploads_bp.route('/init_upload', methods=['POST'])
def init_upload():
    """初始化上传任务"""
    data = request.json
    file_name = secure_filename(data.get('fileName'))
    file_size = data.get('fileSize')
    total_chunks = data.get('totalChunks')
    file_md5 = data.get('fileMd5')

    if not all([file_name, file_size, total_chunks, file_md5]):
        return jsonify({'code': 400, 'msg': '参数不完整'}), 400

    # 检查文件是否已存在
    if os.path.exists(os.path.join(UPLOAD_FOLDER, file_name)):
        return jsonify({
            'code': 0,
            'msg': '文件已存在',
            'data': {'status': 'completed'}
        })

    # 创建文件上传记录
    upload_id = file_md5
    temp_dir = os.path.join(TEMP_FOLDER, upload_id)
    os.makedirs(temp_dir, exist_ok=True)

    # 检查是否有未完成的上传任务
    uploaded_chunks = []
    info_path = os.path.join(temp_dir, 'info.json')
    if os.path.exists(info_path):
        try:
            with open(info_path, 'r') as f:
                existing_info = json.load(f)
                uploaded_chunks = existing_info.get('uploadedChunks', [])
        except:
            # 如果读取失败，使用空列表
            pass

    # 保存上传任务信息
    upload_info = {
        'fileName': file_name,
        'fileSize': file_size,
        'totalChunks': total_chunks,
        'uploadedChunks': uploaded_chunks,
        'fileMd5': file_md5
    }

    with open(info_path, 'w') as f:
        json.dump(upload_info, f)

    return jsonify({
        'code': 0,
        'msg': '上传任务初始化成功',
        'data': {
            'uploadId': upload_id,
            'uploadedChunks': uploaded_chunks
        }
    })

@large_uploads_bp.route('/upload_chunk', methods=['POST'])
def upload_chunk():
    """上传文件分块"""
    upload_id = request.form.get('uploadId')
    chunk_index = int(request.form.get('chunkIndex'))
    file_chunk = request.files.get('file')

    if not all([upload_id, chunk_index is not None, file_chunk]):
        return jsonify({'code': 400, 'msg': '参数不完整'}), 400

    temp_dir = os.path.join(TEMP_FOLDER, upload_id)
    if not os.path.exists(temp_dir):
        return jsonify({'code': 404, 'msg': '上传任务不存在'}), 404

    # 读取上传任务信息
    with open(os.path.join(temp_dir, 'info.json'), 'r') as f:
        upload_info = json.load(f)

    # 保存分块文件
    chunk_file_path = os.path.join(temp_dir, f'chunk_{chunk_index}')
    file_chunk.save(chunk_file_path)

    # 更新已上传分块信息
    if chunk_index not in upload_info['uploadedChunks']:
        upload_info['uploadedChunks'].append(chunk_index)
        upload_info['uploadedChunks'].sort()

    # 保存更新后的上传任务信息
    with open(os.path.join(temp_dir, 'info.json'), 'w') as f:
        json.dump(upload_info, f)

    return jsonify({
        'code': 0,
        'msg': f'分块 {chunk_index} 上传成功',
        'data': {
            'uploadedChunks': upload_info['uploadedChunks']
        }
    })


@large_uploads_bp.route('/merge_chunks', methods=['POST'])
def merge_chunks():
    """合并文件分块"""
    data = request.json
    upload_id = data.get('uploadId')

    if not upload_id:
        return jsonify({'code': 400, 'msg': '参数不完整'}), 400

    temp_dir = os.path.join(TEMP_FOLDER, upload_id)
    if not os.path.exists(temp_dir):
        return jsonify({'code': 404, 'msg': '上传任务不存在'}), 404

    # 读取上传任务信息
    with open(os.path.join(temp_dir, 'info.json'), 'r') as f:
        upload_info = json.load(f)

    # 检查分块是否上传完成
    total_chunks = upload_info['totalChunks']
    uploaded_chunks = upload_info['uploadedChunks']

    if len(uploaded_chunks) != total_chunks:
        missing_chunks = [i for i in range(total_chunks) if i not in uploaded_chunks]
        return jsonify({
            'code': 400,
            'msg': '文件分块未上传完成',
            'data': {
                'uploadedChunks': uploaded_chunks,
                'missingChunks': missing_chunks
            }
        }), 400

    # 合并文件分块
    file_name = upload_info['fileName']
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    with open(file_path, 'wb') as outfile:
        for i in range(total_chunks):
            chunk_path = os.path.join(temp_dir, f'chunk_{i}')
            with open(chunk_path, 'rb') as infile:
                outfile.write(infile.read())

    # 验证文件MD5
    file_md5 = calculate_file_md5(file_path)
    if file_md5 != upload_info['fileMd5']:
        os.remove(file_path)
        return jsonify({
            'code': 400,
            'msg': 'MD5校验失败，文件可能已损坏'
        }), 400

    # 清理临时文件
    shutil.rmtree(temp_dir)

    return jsonify({
        'code': 0,
        'msg': '文件上传成功',
        'data': {
            'fileName': file_name,
            'fileSize': upload_info['fileSize'],
            'fileMd5': file_md5
        }
    })


@large_uploads_bp.route('/upload_status', methods=['GET'])
def upload_status():
    """查询上传状态"""
    upload_id = request.args.get('uploadId')

    if not upload_id:
        return jsonify({'code': 400, 'msg': '参数不完整'}), 400

    temp_dir = os.path.join(TEMP_FOLDER, upload_id)
    if not os.path.exists(temp_dir):
        return jsonify({'code': 404, 'msg': '上传任务不存在'}), 404

    # 读取上传任务信息
    with open(os.path.join(temp_dir, 'info.json'), 'r') as f:
        upload_info = json.load(f)

    return jsonify({
        'code': 0,
        'msg': '获取上传状态成功',
        'data': {
            'fileName': upload_info['fileName'],
            'fileSize': upload_info['fileSize'],
            'totalChunks': upload_info['totalChunks'],
            'uploadedChunks': upload_info['uploadedChunks']
        }
    })
