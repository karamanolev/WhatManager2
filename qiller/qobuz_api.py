import hashlib
import logging
import time
import json

import requests


logger = logging.getLogger(__name__)


class QobuzAPI(object):
    APP_ID = '214748364'
    APP_SECRET = '6fdcbccb7a073f35fbd16a193cdef6c4'
    FLAC_FORMAT_ID = 6

    def __init__(self, username, password, load_state, save_state):
        """
        Creates a Qobuz API
        username -- Qobuz username
        password -- Qobuz password
        load_state -- a function that returns the current state as a string or None if no state
        save_state -- a function that accepts a string argument and persists it for load_state
        """
        state = load_state()
        self.login_data = None
        if state is None:
            logger.debug('There is no state, logging in.')
            self.login_data = self.login(username, password)
            save_state(json.dumps(self.login_data))
        else:
            logger.debug('Found state, looading.')
            self.login_data = json.loads(state)
        self.call('status/test')

    def login(self, username, password):
        password_hash = hashlib.md5(password).hexdigest()
        return self.call('user/login', username=username, password=password_hash)

    def get_request(self, endpoint, **kwargs):
        headers = {
            'X-App-Id': self.APP_ID,
        }
        if self.login_data:
            headers['X-User-Auth-Token'] = self.login_data['user_auth_token']
        url = 'http://www.qobuz.com/api.json/0.2/{0}'.format(endpoint)
        return requests.get(url, params=kwargs, headers=headers)

    def get_file_url(self, track_id, format_id=FLAC_FORMAT_ID):
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
        return self.call('track/getFileUrl', track_id=track_id, format_id=format_id,
                         request_ts=request_ts, request_sig=sig_md5)

    def call(self, endpoint, **kwargs):
        logger.debug('Calling %s params=%s', endpoint, kwargs)
        response = self.get_request(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
