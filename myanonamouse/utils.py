import re
import requests
import pickle
import time

from myanonamouse.models import MAMLoginCache
from myanonamouse.settings import MAM_USERNAME, MAM_PASSWORD, MAM_LOGIN_URL, MAM_ROOT_URL


class MAMException(Exception):
    pass


class LoginException(MAMException):
    pass


def process_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        return url
    elif url.startswith('//'):
        return 'http:' + url
    elif url.startswith('/'):
        return MAM_ROOT_URL + url
    else:
        return MAM_ROOT_URL + '/' + url


class MAMClient(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        try:
            login_cache = MAMLoginCache.objects.get()
            for cookie in pickle.loads(login_cache.cookies):
                self.session.cookies.set_cookie(cookie)
        except MAMLoginCache.DoesNotExist:
            pass

    def _login(self):
        data = {
            'username': self.username,
            'password': self.password,
        }
        r = self.session.post(process_url(MAM_LOGIN_URL), data=data, allow_redirects=False)
        if r.status_code != 302:
            raise LoginException()
        if r.headers['location'] != '/index.php':
            raise LoginException()
        MAMLoginCache.objects.all().delete()
        login_cache = MAMLoginCache(cookies=pickle.dumps([c for c in self.session.cookies]))
        login_cache.save()

    def _request(self, url, try_login):
        resp = self.session.request('GET', url, allow_redirects=False)
        if resp.status_code == 302:
            if resp.headers['location'].startswith('/login.php?'):
                if try_login:
                    self._login()
                    return self._request(url, try_login=False)
                else:
                    raise LoginException()
            else:
                raise MAMException('Request redirect: {0}'.format(resp.headers['location']))
        elif resp.status_code != 200:
            raise MAMException()
        return resp

    def request(self, url):
        return self._request(process_url(url), try_login=True)

    def download_torrent(self, torrent_url):
        for i in range(3):
            try:
                r = self.request(torrent_url)
                if 'application/x-bittorrent' in r.headers['content-type']:
                    filename = re.search('filename="(.*)"',
                                         r.headers['content-disposition']).group(1)
                    return filename, r.content
                else:
                    raise Exception('Wrong status_code or content-type')
            except Exception as ex:
                print('Error while download MAM torrent. Will retry: {0}'.format(ex))
                time.sleep(3)
                download_exception = ex
        raise download_exception

    @staticmethod
    def get():
        return MAMClient(MAM_USERNAME, MAM_PASSWORD)
