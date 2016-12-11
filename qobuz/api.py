import hashlib
import time
import ujson

import requests

from WhatManager2.locking import LockModelTables
from qobuz import settings
from qobuz.models import LoginDataCache


class QobuzAPI(object):
    APP_ID = '214748364'
    APP_SECRET = '6fdcbccb7a073f35fbd16a193cdef6c4'

    def __init__(self, username, password):
        self.login_data = None
        with LockModelTables(LoginDataCache):
            try:
                login_cache = LoginDataCache.objects.get()
                self.login_data = login_cache.data
            except LoginDataCache.DoesNotExist:
                self.login_data = self.login(username, password)
                login_cache = LoginDataCache(
                    data_json=ujson.dumps(self.login_data)
                )
                login_cache.save()
        self.call('status/test')

    def login(self, username, password):
        return self.call('user/login', {
            'username': username,
            'password': hashlib.md5(password).hexdigest(),
        })

    def get_request(self, endpoint, params):
        headers = {
            'X-App-Id': self.APP_ID,
        }
        if self.login_data:
            headers['X-User-Auth-Token'] = self.login_data['user_auth_token']
        return requests.get('http://www.qobuz.com/api.json/0.2/{0}'.format(endpoint),
                            params=params, headers=headers)

    def get_file_url(self, track_id, format_id):
        track_id = str(track_id)
        format_id = str(format_id)
        request_ts = int(time.time())
        sig = 'trackgetFileUrl{0}{1}{2}{3}'.format(
            'format_id' + format_id,
            'track_id' + track_id,
            request_ts,
            self.APP_SECRET,
        )
        sig_md5 = hashlib.md5(sig).hexdigest()
        return self.call('track/getFileUrl', params={
            'track_id': track_id,
            'format_id': format_id,
            'request_ts': request_ts,
            'request_sig': sig_md5,
        })

    def call(self, endpoint, params=None):
        response = self.get_request(endpoint, params or {})
        response.raise_for_status()
        return response.json()


def get_qobuz_client(request):
    if not hasattr(request, 'qobuz_client'):
        request.qobuz_client = QobuzAPI(settings.QOBUZ_USERNAME, settings.QOBUZ_PASSWORD)
    return request.qobuz_client


# print get_request('status/test', {}).json()

# album = get_request('album/get', {
# 'album_id': '3760002131573',
# })

# track = get_file_url('3691440', '5')
