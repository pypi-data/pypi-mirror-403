# @Time   : 2024-05-15
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import time
import json
from bson import ObjectId
from hfwm.models.databases.handle import DataHandle
from hfwm.models.common import assert_condition
from hfwm.models.auth import Auth

try:
    with open(relative_conf_path('message_channels.json'), 'r') as f:
        message_channels = json.load(f)
except:
    message_channels = []


def send_msg(data):
    auth_table = DataHandle.get_table('auth')

    target_users = data["targetUsers"]
    channel = data["channel"]
    title = data["title"]
    content = data["content"]
    expire_day = int(data["expireDay"])
    assert_condition(channel in message_channels, 400, "该频道不存在")
    assert_condition(auth_table.count_documents({'username': {'$in': target_users}}) == len(target_users), 400,
                     "用户不存在")

    send_user = Auth.current().username

    find_items = DataHandle.get_table('messageQueue').find(
        {'channel': channel, 'title': title, 'content': content, 'processed': 'incomplete'})

    sent_targets = []

    for find_item in find_items:
        if find_item['targetUser'] not in sent_targets:
            sent_targets.append(find_item['targetUser'])

    expire_time = TimeNow().ymdhms(time.time() + 60 * 60 * 24 * expire_day)
    target_users.append('')  # 发任务的存储
    group_id = str(ObjectId())
    count = 0
    for user in target_users:
        if user in sent_targets:
            continue
        if user != '':
            count += 1
        data = {
            'sendUser': send_user,
            'targetUser': user,
            'channel': channel,
            'groupId': group_id,
            'title': title,
            'content': content,
            'expireTime': expire_time,
            'createTime': TimeNow().ymdhms(),
            'status': "read" if user == '' else 'sent',
            'processed': 'incomplete',
            'processedUser': '',
        }
        DataHandle.get_table('messageQueue').insert_one(data)
    return count


def find_messages(data, recv_or_send):
    page_num = int(data['pageNum']) - 1
    assert_condition(page_num >= 0, 400, "页面编号需为非负数")
    page_size = int(data['pageSize'])
    assert_condition(0 < page_size <= 500, 400, "page_size 取值范围是1-100")
    processed = data['processed']

    channel = data.get('channel')
    if channel is not None:
        assert_condition(channel in message_channels, 400, "该频道不存在")
    if recv_or_send == 'recv':
        status = data['status']

    else:
        status = ['read']

    if isinstance(status, str):
        status = [status]
    if isinstance(processed, str):
        processed = [processed]

    for it in status:
        assert_condition(it in ['sent', 'read'], 400, "查询状态错误")
    for it in processed:
        assert_condition(it in ['incomplete', 'complete'], 400, "查询处理状态错误")

    table = DataHandle.get_table('messageQueue')
    if recv_or_send == 'recv':
        query = {"targetUser": Auth.current().username, "status": {"$in": status}, 'processed': {'$in': processed}}
    else:
        query = {"sendUser": Auth.current().username, 'targetUser': '', 'processed': {'$in': processed}}
    if channel is not None:
        query['channel'] = channel
    total_num = table.count_documents(query)
    items = table.find(query).sort('_id', -1).skip(page_num * page_size).limit(page_size)
    records = list()
    cur_time = TimeNow().ymdhms()
    for it in items:
        if it['expireTime'] < cur_time:
            table.delete_one({'_id': it['_id']})
            continue
        it['id'] = str(it['_id'])
        it.pop('_id')
        records.append(it)
    return {"totalNum": total_num, "records": records}


def find_one_message(message_id):
    table = DataHandle.get_table('messageQueue')
    query = {"_id": ObjectId(message_id)}
    item = table.find_one(query)
    if item is None:
        return None
    if item['expireTime'] < TimeNow().ymdhms():
        table.delete_one({'_id': item['_id']})
        return None
    table.update_one(query, {'$set': {'status': 'read'}}, upsert=False)
    item['id'] = str(item['_id'])
    item.pop('_id')
    return item


def process_message(group_id):
    user = Auth.current().username
    return DataHandle.get_table('messageQueue').update_many({'groupId': group_id, 'targetUser': {'$in': [user, '']}},
                                                            {'$set': {'processedUser': user, 'processed': 'complete'}},
                                                            upsert=False).modified_count


def delete_message(group_id):
    user = Auth.current().username
    return DataHandle.get_table('messageQueue').delete_many({'groupId': group_id, 'targetUser': user}).deleted_count + \
        DataHandle.get_table('messageQueue').delete_many({'groupId': group_id, 'sendUser': user}).deleted_count
