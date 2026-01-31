# @Time   : 2025-07-17
# @Author : zhangxinhao
# @Compile : True


from urllib.parse import urlparse


def parse_redis_url(url):
    parsed = urlparse(url)
    username = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port

    path_parts = parsed.path.lstrip('/').split('/')
    db = path_parts[0] if len(path_parts) > 0 and path_parts[0] else None
    url = '/' + '/'.join(path_parts[1:])

    redis_conf = {
        'host': host,
        'port': port,
        'db': int(db)
    }
    if username:
        redis_conf['username'] = username
    if password:
        redis_conf['password'] = password
    return redis_conf, url
