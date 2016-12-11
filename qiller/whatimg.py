import pyquery
import requests


def login(session, username, password):
    params = {
        'act': 'login-d',
    }
    payload = {
        'username': username,
        'password': password,
    }
    session.post('https://whatimg.com/users.php', params=params, data=payload)


def upload_image_from_memory(username, password, album_id, data):
    session = requests.Session()
    login(session, username, password)
    files = {
        'userfile[]': ('image.jpg', data),
    }
    payload = {
        'upload_to': album_id,
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
