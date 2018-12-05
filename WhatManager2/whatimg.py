import requests
import json

from WhatManager2 import settings


def login(session):
    payload = {
        'email': settings.WHATIMG_USERNAME,
        'pass': settings.WHATIMG_PASSWORD,
    }
    r = session.post('https://ptpimg.me/login.php', data=payload)
    pq = pyquery.PyQuery(r.text)
    api_key = pq('input').attr('value')
    return api_key

def upload_image_from_memory(album_id, data):
    session = requests.Session()
    api_key = login(session)
    files = {
        'file-upload[]': ('image.jpg', data),
    }
    payload = {
        'api_key': api_key
    }
    r = session.post('https://ptpimg.me/upload.php', files=files)
    if r.status_code != requests.codes.ok:
        raise Exception('Error during uploading: error code {0}'.format(r.status_code))
    j = json.loads(r.text)
    link = 'https://ptpimg.me/{}.{}'.format(j[0]['code'], j[0]['ext'])
    return link
