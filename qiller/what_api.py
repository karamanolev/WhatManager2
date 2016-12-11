import logging
import pickle
import json

import requests


WHAT_CD_DOMAIN = 'what.cd'

headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept-Charset': 'utf-8',
    'User-Agent': 'whatapi [isaaczafuta]'
}

logger = logging.getLogger(__name__)


class LoginException(Exception):
    pass


class RequestException(Exception):
    def __init__(self, message=None, response=None):
        super(Exception, self).__init__(message)
        self.response = response


class BadIdException(RequestException):
    def __init__(self, response=None):
        super(BadIdException, self).__init__('Bad ID Parameter.', response)


class RateLimitExceededException(RequestException):
    def __init__(self, response=None):
        super(RateLimitExceededException, self).__init__('Rate limit exceeded.', response)


class CustomWhatAPI:
    def __init__(self, username, password, load_state, save_state):
        self.session = requests.Session()
        self.session.headers = headers
        self.authkey = None
        self.passkey = None
        self.username = username
        self.password = password
        self.load_state = load_state
        self.save_state = save_state
        self._login()

    def _login(self):
        try:
            state = json.loads(self.load_state())
            for cookie in pickle.loads(state['cookies']):
                self.session.cookies.set_cookie(cookie)
            self.authkey = state['authkey']
            self.passkey = state['passkey']
            self.request('index')
            logger.debug('Successfully logged in')
        except Exception:
            logger.debug('Exception logging in, making a new login')
            '''Logs in user and gets authkey from server'''
            loginpage = 'https://{0}/login.php'.format(WHAT_CD_DOMAIN)
            data = {
                'username': self.username,
                'password': self.password,
                'keeplogged': 1,
                'login': 'Login',
            }
            r = self.session.post(loginpage, data=data, allow_redirects=False)
            if r.status_code != 302:
                raise LoginException
            accountinfo = self.request("index")
            self.authkey = accountinfo["response"]["authkey"]
            self.passkey = accountinfo["response"]["passkey"]
            state = {
                'authkey': self.authkey,
                'passkey': self.passkey,
                'cookies': pickle.dumps([c for c in self.session.cookies])
            }
            self.save_state(json.dumps(state))

    def request(self, action, **kwargs):
        '''Makes an AJAX request at a given action page'''
        ajaxpage = 'https://{0}/ajax.php'.format(WHAT_CD_DOMAIN)
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)

        r = self.session.get(ajaxpage, params=params, allow_redirects=False)
        try:
            json_response = r.json()
            if json_response["status"] != "success":
                if json_response['error'] == 'bad id parameter':
                    raise BadIdException(json_response)
                elif json_response['error'] == 'rate limit exceeded':
                    raise RateLimitExceededException(json_response)
                raise RequestException(
                    message=json_response['error'] if 'error' in json_response else json_response,
                    response=json_response)
            return json_response
        except ValueError:
            raise RequestException()
