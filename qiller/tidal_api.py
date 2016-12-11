import logging

import requests


logger = logging.getLogger(__name__)


class TidalAPI(object):
    def __init__(self, session_id):
        self.session_id = session_id

    def call(self, *args):
        url = 'https://listen.tidalhifi.com/v1/' + '/'.join(args)
        params = {
            'sessionId': self.session_id,
            'countryCode': 'US',
        }
        if 'streamUrl' in args:
            params['soundQuality'] = 'LOSSLESS'
        response = requests.get(url, params=params, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36'
        })
        return response.json()
