# @Time   : 2023-10-26
# @Author : zhangxinhao
# @Compile : True
from aixm.utils import *
import time
import traceback


def main():
    init_logger('pubsub_heart')
    conn = redis_conn()
    while True:
        try:
            time.sleep(10)
            channels = conn.pubsub_channels()
            for channel in channels:
                if isinstance(channel, bytes):
                    channel = channel.decode()
                if channel.startswith('HFWM_SSE_PUBLISH'):
                    conn.publish(channel, 'heartbeat')
        except:
            log().error(traceback.format_exc())
