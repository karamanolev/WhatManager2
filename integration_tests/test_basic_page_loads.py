from django.contrib.auth.models import User
from django.test import testcases
from django.test.client import Client


class TestBasicPageLoads(testcases.TestCase):
    def setUp(self):
        super(TestBasicPageLoads, self).setUp()

        u = User(username='john_doe')
        u.set_password('password')
        u.is_superuser = True
        u.save()

        self.client = Client()

    def login(self):
        response = self.client.post('/user/login',
                                    {'username': 'john_doe', 'password': 'password'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://testserver/')

    def test_require_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://testserver/user/login?next=/')

    def test_login(self):
        response = self.client.post('/user/login?next=/',
                                    {'username': 'john_doe', 'password': 'password'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://testserver/')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_correct(self):
        response = self.client.post('/user/login?next=/dummy_url',
                                    {'username': 'john_doe', 'password': 'password'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://testserver/dummy_url')

    def test_book_uploads(self):
        self.login()
        response = self.client.post('/books/uploads')
        self.assertEqual(response.status_code, 200)

    def test_view_log(self):
        self.login()
        response = self.client.post('/view_log')
        self.assertEqual(response.status_code, 200)

    def test_checks(self):
        self.login()
        response = self.client.post('/checks')
        self.assertEqual(response.status_code, 200)

    def test_torrents(self):
        self.login()
        response = self.client.post('/torrents')
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        self.login()
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)

    def test_queue(self):
        self.login()
        response = self.client.get('/queue/')
        self.assertEqual(response.status_code, 200)

    def test_stats(self):
        self.login()
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)

    def test_userscripts(self):
        self.login()
        response = self.client.get('/userscripts')
        self.assertEqual(response.status_code, 200)

    def test_part_torrent_stats(self):
        self.login()
        response = self.client.get('/part/torrent_stats')
        self.assertEqual(response.status_code, 200)

    def test_part_recent_log(self):
        self.login()
        response = self.client.post('/part/recent_log',
                                    {'log_types': 'error,action,info', 'count': 10})
        self.assertEqual(response.status_code, 200)

    def test_part_error_torrents(self):
        self.login()
        response = self.client.get('/part/error_torrents')
        self.assertEqual(response.status_code, 200)

    def test_part_downloading(self):
        self.login()
        response = self.client.get('/part/downloading')
        self.assertEqual(response.status_code, 200)

    def test_part_recently_downloaded(self):
        self.login()
        response = self.client.get('/part/recently_downloaded')
        self.assertEqual(response.status_code, 200)

    def test_part_queue_stats(self):
        self.login()
        response = self.client.get('/queue/part/queue_stats')
        self.assertEqual(response.status_code, 200)
