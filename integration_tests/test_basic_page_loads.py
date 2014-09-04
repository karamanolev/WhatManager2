from django.contrib.auth.models import User
from django.test import testcases
from django.test.client import Client


class Fail(testcases.TestCase):
    def setUp(self):
        super(Fail, self).setUp()

        u = User(username='john_doe')
        u.set_password('password')
        u.is_superuser = True
        u.save()

        self.client = Client()

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

    def test_profile(self):
        self.client.post('/user/login',
                         {'username': 'john_doe', 'password': 'password'})
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
