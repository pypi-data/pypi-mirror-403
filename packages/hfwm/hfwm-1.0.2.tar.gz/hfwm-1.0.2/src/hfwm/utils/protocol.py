# @Time   : 2020-10-22
# @Author : zhangxinhao
# @Compile : True
import time
import json
import hashlib
import math
from Crypto.Cipher import Blowfish
import codecs
import random

secret = "DC355330E75440308FB27737E17BA9C8"

blowfish_secret = "4eF2A4a9+89/4F=D"


def blowfish_encrypt_pck5(data, key):
    data = data.encode('utf-8')
    pad_len = 8 - (len(data) % 8)
    data += bytes([pad_len] * pad_len)
    key = key.encode("utf-8")
    cl = Blowfish.new(key, Blowfish.MODE_ECB)
    encode = cl.encrypt(data)
    hex_encode = codecs.encode(encode, 'hex_codec')
    return hex_encode.decode()


def blowfish_decrypt_pck5(data, key):
    key = key.encode("utf-8")
    data = data.encode("utf-8")
    cl = Blowfish.new(key, Blowfish.MODE_ECB)
    ciphertext = codecs.decode(data, 'hex_codec')  # 可以根据自己需要更改hex_codec
    code = cl.decrypt(ciphertext)
    pad_len = code[-1]
    return code[:-pad_len].decode()


def encode(data, uid, secretx=None, blowfish_secretx=None):
    if secretx is None:
        secretx = secret
    if blowfish_secretx is None:
        blowfish_secretx = blowfish_secret
    nonce = str(random.randint(10000, 10000000))
    timestamp = str(int(time.time()))
    data = json.dumps(data)
    en_str = "%sData=%s&Nonce=%s&Timestamp=%s%s" % (secretx, data, nonce, timestamp, uid)
    authorization = hashlib.md5(en_str.encode()).hexdigest()
    version = "%s&%s&%s" % (uid, secretx, blowfish_secretx)
    V = hashlib.md5(version.encode()).hexdigest()
    body = {
        'Timestamp': timestamp,
        'Nonce': nonce,
        'Data': data,
        'Authorization': authorization
    }
    return {'Body' :blowfish_encrypt_pck5(json.dumps(body), blowfish_secretx),
            'SN': uid, 'V': V}



def decode(body_dict, secretx=None, blowfish_secretx=None):
    if secretx is None:
        secretx = secret
    if blowfish_secretx is None:
        blowfish_secretx = blowfish_secret
    enbody = body_dict['Body']
    SN = body_dict['SN']
    remote_secert_V = body_dict['V']
    version = "%s&%s&%s" % (SN, secretx, blowfish_secretx)
    local_secert_V = hashlib.md5(version.encode()).hexdigest()
    if remote_secert_V != local_secert_V:
        raise Exception("protocol decode secert v 不一致")

    data = json.loads(blowfish_decrypt_pck5(enbody, blowfish_secretx))
    cur_timestamp = time.time()
    timestamp = int(data['Timestamp'])
    if math.fabs(cur_timestamp - timestamp) > 300:
        raise Exception("protocol decode t 不一致")
    nonce = data['Nonce']
    data_body = data['Data']
    authorization = data['Authorization']
    en_str = "%sData=%s&Nonce=%s&Timestamp=%s%s" % (secretx, data_body, nonce, timestamp, SN)
    check_authorization = hashlib.md5(en_str.encode()).hexdigest()
    if authorization != check_authorization:
        raise Exception('protocol decode authorization != check_authorization')
    return json.loads(data_body)


def request_args_check(args):
    req_time = int(args.get("time"))
    req_id = args.get('id')
    req_code = args.get('code')
    cur_time = time.time()
    if math.fabs(cur_time - int(req_time)) > 300:
        raise Exception("request_args_check t 不一致")
    en_str = req_id + secret + str(req_time)
    check_code = hashlib.md5(en_str.encode()).hexdigest()
    if req_code != check_code:
        raise Exception("req_code != check_code")




