import HTMLParser
import base64
from contextlib import contextmanager
from functools import wraps
import hashlib
import hmac
import json
import re
import urllib

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
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
        return HttpResponse(json.dumps(val, indent=True), content_type='text/json')

    return wrapped


def html_unescape(data):
    html_parser = HTMLParser.HTMLParser()
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
    bin_sig = hmac.new(SECRET_KEY, plaintext, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(bin_sig)


def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.urlencode(get)
    return url


def get_user_token(user):
    return wm_hmac(user.username)


def auth_username_token(fn):
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated():
            try:
                user = User.objects.get(username=request.GET.get('username'))
            except User.DoesNotExist:
                return redirect('login.views.login')
            if get_user_token(user) != request.GET['token']:
                return redirect('login.views.login')
            request.user = user
        return fn(request, *args, **kwargs)

    return inner


def wm_unicode(s):
    if isinstance(s, str):
        return s.decode('utf-8')
    elif isinstance(s, unicode):
        return s
    raise Exception('Unknown string type: {0}'.format(type(s)))


def wm_str(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    elif isinstance(s, str):
        return s
    raise Exception('Unknown string type: {0}'.format(type(s)))


def get_artists(group):
    a_main = group['musicInfo']['artists']
    a_composers = group['musicInfo']['composers']
    a_conductors = group['musicInfo']['conductor']
    a_djs = group['musicInfo']['dj']

    if len(a_main) == 0 and len(a_conductors) == 0 and len(a_djs) == 0 and len(a_composers) == 0:
        return ''

    link = []

    if len(a_composers) and len(a_composers) < 3:
        link.append(' & '.join(html_unescape(a['name']) for a in a_composers))

        if len(a_composers) < 3 and len(a_main) > 0:
            link.append('performed by')

    composer_str = list(link)

    if len(a_main):
        if len(a_main) <= 2:
            link.append(' & '.join(html_unescape(a['name']) for a in a_main))
        else:
            link.append('Various Artists')

    if len(a_conductors):
        if (len(a_main) or len(a_composers)) and (len(a_composers) < 3 or len(a_main)):
            link.append('under')

        if len(a_conductors) <= 2:
            link.append(' & '.join(html_unescape(a['name']) for a in a_conductors))
        else:
            link.append('Various Conductors')

    if len(a_composers) and len(a_main) + len(a_conductors) > 3 and len(a_main) > 1 and len(
            a_conductors) > 1:
        link = composer_str
        link.append('Various Artists')
    elif len(a_composers) > 2 and len(a_main) + len(a_conductors) == 0:
        link = ['Various Composers']

    if len(a_djs):
        if len(a_djs) <= 2:
            link = [' & '.join(html_unescape(a['name']) for a in a_djs)]
        else:
            link = ['Various DJs']

    return ' '.join(link)


def read_text(path):
    with open(path, 'rb') as f:
        return f.read()


def write_text(path, text):
    with open(path, 'wb') as f:
        f.write(text)
