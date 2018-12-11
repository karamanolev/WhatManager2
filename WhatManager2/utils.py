import html.parser
import base64
from contextlib import contextmanager
from functools import wraps
import hashlib
import hmac
import ujson
import re
import urllib.request, urllib.parse, urllib.error
import stat
import os
import errno

from django.contrib.auth.models import User
from django.urls import reverse
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from WhatManager2.settings import SECRET_KEY


WHAT_DOWNLOAD_LINK_RE = re.compile(re.escape('torrents.php?action=download&id=') + '(\d+)')


@contextmanager
def dummy_context_manager(*args, **kwargs):
    yield


def json_return_method(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        val = fn(*args, **kwargs)
        if type(val) is HttpResponse:
            return val
        return HttpResponse(ujson.dumps(val), content_type='text/json')

    return wrapped


def html_unescape(data):
    html_parser = html.parser.HTMLParser()
    return html_parser.unescape(data)


def norm_hash(hash):
    return hash.upper()


def norm_t_torrent(t):
    t.hashString = norm_hash(t.hashString)
    if 'addedDate' in t._fields:
        t.date_added_tz = timezone.make_aware(t.date_added, timezone.get_default_timezone())


def match_properties(a, b, props):
    for prop in props:
        if getattr(a, prop[0]) != getattr(b, prop[1]):
            return False
    return True


def copy_properties(a, b, props):
    for prop in props:
        setattr(a, prop[0], getattr(b, prop[1]))


def wm_hmac(plaintext):
    bin_sig = hmac.new(SECRET_KEY, plaintext.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(bin_sig)


def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.parse.urlencode(get)
    return url


def get_user_token(user):
    return wm_hmac(user.username)


def auth_username_token(fn):
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            try:
                user = User.objects.get(username=request.GET.get('username'))
            except User.DoesNotExist:
                return redirect('login.views.login')
            if get_user_token(user) != request.GET['token']:
                return redirect('login.views.login')
            request.user = user
        return fn(request, *args, **kwargs)

    return inner


class JoinedArtistsBuilder(object):
    def __init__(self, joined_artists_builder=None):
        if joined_artists_builder is None:
            self.result = []
        else:
            self.result = list(joined_artists_builder.result)

    def append_joined(self, join_string, artists):
        for a in artists:
            self.result.append({
                'id': a['id'],
                'name': a['name'],
                'join': join_string,
            })
        self.result[-1]['join'] = ''

    def append_artist(self, artist):
        self.result.append({
            'id': artist['id'],
            'name': html_unescape(artist['name']),
            'join': '',
        })

    def append_join(self, join_string):
        assert not self.result[-1]['join'], 'Last join should be empty before adding a new join'
        self.result[-1]['join'] = join_string

    def clear(self):
        self.result = []


def get_artists_list(group):
    a_main = group['musicInfo']['artists']
    a_composers = group['musicInfo']['composers']
    a_conductors = group['musicInfo']['conductor']
    a_djs = group['musicInfo']['dj']

    if len(a_main) == 0 and len(a_conductors) == 0 and len(a_djs) == 0 and len(a_composers) == 0:
        return []

    builder = JoinedArtistsBuilder()

    if len(a_composers) and len(a_composers) < 3:
        builder.append_joined(' & ', a_composers)
        if len(a_composers) < 3 and len(a_main) > 0:
            builder.append_join(' performed by ')

    composer_builder = JoinedArtistsBuilder(builder)

    if len(a_main):
        if len(a_main) <= 2:
            builder.append_joined(' & ', a_main)
        else:
            builder.append_artist({'id': -1, 'name': 'Various Artists'})

    if len(a_conductors):
        if (len(a_main) or len(a_composers)) and (len(a_composers) < 3 or len(a_main)):
            builder.append_join(' under ')
        if len(a_conductors) <= 2:
            builder.append_joined(' & ', a_conductors)
        else:
            builder.append_artist({'id': -1, 'name': 'Various Conductors'})

    if len(a_composers) and len(a_main) + len(a_conductors) > 3 and len(a_main) > 1 and len(
            a_conductors) > 1:
        builder = composer_builder
        builder.append_artist({'id': -1, 'name': 'Various Artists'})
    elif len(a_composers) > 2 and len(a_main) + len(a_conductors) == 0:
        builder.clear()
        builder.append_artist({'id': -1, 'name': 'Various Composers'})

    if len(a_djs):
        if len(a_djs) <= 2:
            builder.clear()
            builder.append_joined(' & ', a_djs)
        else:
            builder.clear()
            builder.append_artist({'id': -1, 'name': 'Various DJs'})

    return builder.result


def get_artists(group):
    artists_list = get_artists_list(group)
    result = []
    for a in artists_list:
        result.append(a['name'])
        result.append(a['join'])
    return ''.join(result)


def read_text(path):
    with open(path, 'r') as f:
        return f.read()


def write_text(path, text):
    with open(path, 'w') as f:
        f.write(text)

def attemptFixPermissions(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        # change the file to be readable,writable,executable: 0777
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  
        # retry
        func(path)
    else:
        raise exc[1]
