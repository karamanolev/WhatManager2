import re
import shutil
import time
import os
import os.path

from pyquery.pyquery import PyQuery
import requests
import requests.utils

from WhatManager2.settings import MEDIA_ROOT
from bibliotik import manage_bibliotik
from bibliotik.models import BibliotikTorrent, BibliotikFulltext
from bibliotik.settings import BIBLIOTIK_UPLOAD_URL, BIBLIOTIK_DOWNLOAD_TORRENT_URL
from home.models import DownloadLocation


def extract_torrents(html):
    result = []
    pq = PyQuery(html)
    for row in list(pq('#torrents_table tbody tr.torrent').items()):
        data = {
            'id': row.attr('id')[len('torrent-'):],
            'type': row('td:eq(0) img').attr('title'),
            'title': row('td:eq(1) span.title').text(),
            'publishers': [],
            'authors': [],
            'year': row('td:eq(1) span.torYear').text()[1:-1],
            'format': row('td:eq(1) span.torFormat').text()[1:-1],
            'retail': bool(row('td:eq(1) span.torRetail')),
            'tags': []
        }
        for dlink in list(row('td:eq(1) > a').items()):
            href = dlink.attr('href')
            if '/creators/' in href:
                data['authors'].append({
                    'id': href[href.rfind('/') + 1:],
                    'name': dlink.text()
                })
            elif '/publishers/' in href:
                data['publishers'].append({
                    'id': href[href.rfind('/') + 1:],
                    'name': dlink.text()
                })
        for tag in list(row('td:eq(1) > span.taglist > a').items()):
            href = tag.attr('href')
            data['tags'].append({
                'id': href[href.rfind('/') + 1:],
                'name': tag.text()
            })
        result.append(data)
    return result


class BibliotikClient(object):
    def __init__(self, session_id):
        self.session_id = session_id
        self.session = requests.Session()
        requests.utils.add_dict_to_cookiejar(self.session.cookies, {
            'id': session_id
        })
        self.auth_key = None

    def get_auth_key(self):
        if self.auth_key:
            return self.auth_key
        for i in range(3):
            try:
                response = self.session.get('https://bibliotik.me/upload/ebooks')
                response.raise_for_status()
                break
            except Exception:
                pass
        response.raise_for_status()
        pq = PyQuery(response.content)
        self.auth_key = pq('input[name="authkey"]').val()
        if not self.auth_key:
            raise Exception('Could not get the authkey')
        return self.auth_key

    def send_upload(self, payload, payload_files):
        return self.session.post(BIBLIOTIK_UPLOAD_URL, data=payload, files=payload_files,
                                 allow_redirects=False)

    def download_torrent(self, torrent_id):
        torrent_page = BIBLIOTIK_DOWNLOAD_TORRENT_URL.format(torrent_id)
        for i in range(3):
            try:
                r = self.session.get(torrent_page, allow_redirects=False)
                r.raise_for_status()
                if r.status_code == 200 and 'application/x-bittorrent' in r.headers['content-type']:
                    filename = re.search('filename="(.*)"',
                                         r.headers['content-disposition']).group(1)
                    return filename, r.content
                else:
                    raise Exception('Wrong status_code or content-type')
            except Exception as ex:
                print('Error while download bibliotik torrent. Will retry: {0}'.format(ex))
                time.sleep(3)
                download_exception = ex
        raise download_exception

    def search(self, query):
        url = 'https://bibliotik.me/torrents/'
        response = self._search_request(url, query)
        if not response.url.startswith(url):
            raise Exception('Search redirected to {0}. Probably invalid id. Was {1}.'.format(
                response.url, self.session_id
            ))
        return {
            'results': extract_torrents(response.content),
        }

    def _search_request(self, url, query):
        for i in range(3):
            try:
                response = self.session.get(url, params={
                    'search': query
                })
                response.raise_for_status()
                return response
            except Exception as ex:
                time.sleep(3)
                exception = ex
        raise exception


def upload_book_to_bibliotik(bibliotik_client, book_upload):
    print('Sending request for upload to bibliotik.me')

    payload_files = dict()
    payload_files['TorrentFileField'] = ('torrent.torrent', book_upload.bibliotik_torrent_file)

    payload = dict()
    payload['upload'] = ''
    payload['authkey'] = bibliotik_client.get_auth_key()
    payload['AuthorsField'] = book_upload.author
    payload['TitleField'] = book_upload.title
    payload['IsbnField'] = book_upload.isbn or ''
    payload['PublishersField'] = book_upload.publisher
    payload['PagesField'] = book_upload.pages or ''
    payload['YearField'] = book_upload.year
    payload['FormatField'] = {
        'AZW3': '21',
        'EPUB': '15',
        'PDF': '2',
    }[book_upload.format]
    payload['LanguageField'] = '1'  # English
    if book_upload.retail:
        payload['RetailField'] = '1'
    payload['TagsField'] = ','.join(book_upload.tag_list)
    payload['ImageField'] = book_upload.cover_url
    payload['DescriptionField'] = book_upload.description

    response = bibliotik_client.send_upload(payload, payload_files)
    response.raise_for_status()
    if response.status_code == requests.codes.ok:
        with open(os.path.join(MEDIA_ROOT, 'bibliotik_upload.html'), 'wb') as f:
            f.write(response.content)
        raise Exception('Bibliotik does not want this. Written to media/')
    redirect_match = re.match('^https://bibliotik.me/torrents/(?P<id>\d+)$',
                              response.headers['location'])
    if not redirect_match:
        raise Exception('Could not get new torrent ID.')
    torrent_id = redirect_match.groupdict()['id']

    book_upload.bibliotik_torrent = BibliotikTorrent.get_or_create(bibliotik_client, torrent_id)
    book_upload.save()

    # Add the torrent to the client
    location = DownloadLocation.get_bibliotik_preferred()
    download_dir = os.path.join(location.path, str(book_upload.bibliotik_torrent.id))
    book_path = os.path.join(download_dir, book_upload.target_filename)
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    os.chmod(download_dir, 0o777)
    shutil.copyfile(
        book_upload.book_data.storage.path(book_upload.book_data),
        book_path
    )
    os.chmod(book_path, 0o777)

    manage_bibliotik.add_bibliotik_torrent(
        book_upload.bibliotik_torrent.id, location=location, bibliotik_client=bibliotik_client
    )

    return book_upload


def search_torrents(query):
    b_fulltext = BibliotikFulltext.objects.only('id').all()
    b_fulltext = b_fulltext.extra(where=['MATCH(`info`, `more_info`) AGAINST (%s IN BOOLEAN MODE)'],
                                  params=[query])
    b_fulltext = b_fulltext.extra(select={'score': 'MATCH (`info`) AGAINST (%s)'},
                                  select_params=[query])
    b_fulltext = b_fulltext.extra(order_by=['-score'])

    b_torrents_dict = BibliotikTorrent.objects.in_bulk([b.id for b in b_fulltext])
    b_torrents = list()
    for i in b_fulltext:
        b_torrent = b_torrents_dict[i.id]
        coef = 1.0
        if b_torrent.retail:
            coef *= 1.2
        if b_torrent.format == 'EPUB':
            coef *= 1.1
        elif b_torrent.format == 'PDF':
            coef *= 0.9
        b_torrent.score = i.score * coef
        b_torrents.append(b_torrent)
    return b_torrents
