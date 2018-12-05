import os
import os.path
import urllib.request, urllib.parse, urllib.error
import datetime
import time

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.utils.http import parse_http_date_safe, http_date
from django.views.decorators.http import last_modified
import requests
from requests.exceptions import ConnectionError

from WhatManager2.settings import MEDIA_ROOT


def get_image_cache_path(url):
    return os.path.join(MEDIA_ROOT, 'what_image_cache', urllib.parse.quote(url, ''))


def get_image_last_modified(request):
    url = request.GET.get('url')
    if not url:
        return None
    image_path = get_image_cache_path(url)
    try:
        s = os.path.getmtime(image_path)
        return datetime.datetime.utcfromtimestamp(s)
    except OSError:
        return None


@login_required
@last_modified(get_image_last_modified)
def image(request):
    url = request.GET.get('url')
    if not url:
        return HttpResponseNotFound('Provide a url get param')
    image_path = get_image_cache_path(url)
    if os.path.isfile(image_path):
        image_file = open(image_path, 'rb')
        return HttpResponse(image_file, content_type='image/' + os.path.splitext(image_path)[1][1:])

    try:
        response = requests.get(url)
    except ConnectionError:
        return HttpResponseNotFound('Error connecting to image host')
    if response.status_code != 200:
        return HttpResponseNotFound('Not Found')
    if 'Last-Modified' in response.headers:
        modified = parse_http_date_safe(response.headers['Last-Modified'])
    else:
        modified = time.mktime(timezone.now().utctimetuple())
    with open(image_path, 'wb') as image_file:
        image_file.write(response.content)
    os.utime(image_path, (int(modified), int(modified)))
    response = HttpResponse(response.content, content_type=response.headers['Content-Type'])
    response['Last-Modified'] = http_date(modified)
    return response
