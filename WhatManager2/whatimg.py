import pyquery
import requests

from WhatManager2 import settings


def login(session):
    params = {
        'act': 'login-d',
    }
    payload = {
        'username': settings.WHATIMG_USERNAME,
        'password': settings.WHATIMG_PASSWORD,
    }
    session.post('https://whatimg.com/users.php', params=params, data=payload)


def upload_image_from_memory(data):
    session = requests.Session()
    login(session)
    files = {
        'userfile[]': ('image.jpg', data),
    }
    payload = {
        'upload_to': '4459',
        'private_upload': '1',
        'upload_type': 'standard',
    }
    r = session.post('https://whatimg.com/upload.php', files=files, data=payload)
    if r.status_code != requests.codes.ok:
        raise Exception(u'Error during uploading: error code {0}'.format(r.status_code))
    pq = pyquery.PyQuery(r.text)
    link = pq('input.input_field:first')
    if len(link) == 0:
        raise Exception(u'Error during uploading: no links found')
    return link.val()
