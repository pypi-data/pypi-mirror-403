# @Time   : 2023-07-03
# @Author : zhangxinhao
# @Compile : True
import os
import json
import time

import requests


class Requests:
    def __init__(self, address, user=None, password=None):
        self.address = address
        if self.address.endswith('/'):
            self.address = self.address[:-1]
        self.user = user
        self.password = password
        self.headers = {}
        self.last_login_time = 0
        self.login(user, password)

    def login(self, user, password):
        self.user = user
        self.password = password
        if self.user is not None:
            r = requests.post(self.address + '/wapi/auth/login', json={
                'username': self.user,
                'password': self.password
            })
            self.headers = {
                'Authorization': r.json()['data']
            }
            self.last_login_time = time.time()

    def re_login(self):
        if time.time() - self.last_login_time > 60 * 8:
            self.login(self.user, self.password)

    def _get_url(self, url):
        self.re_login()
        if not url.startswith('/'):
            url = '/' + url
        return self.address + url

    def get(self, url):
        r = requests.get(self._get_url(url), headers=self.headers)
        if r.status_code != 200:
            print('error code:', r.status_code)
        return r.json()

    def post(self, url, data):
        r = requests.post(self._get_url(url), json=data, headers=self.headers)
        if r.status_code != 200:
            print('error code:', r.status_code)
        return r.json()

    def upload(self, filepath):
        with open(filepath, 'rb') as f:
            files = {"file": (os.path.basename(filepath), f)}
            r = requests.post(self._get_url('/wapi/upload'), files=files, headers=self.headers, timeout=60).json()
            return r['data']
