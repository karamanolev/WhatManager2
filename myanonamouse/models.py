import re
import time
import os.path

import bencode

from django.db import models

from django.utils import timezone

from pyquery.pyquery import PyQuery

from home.models import TransTorrentBase
from myanonamouse.settings import MAM_GET_TORRENT_URL
from what_transcode.utils import get_info_hash_from_data


def load_mam_data(mam_client, torrent_id):
    exception = None
    for i in range(3):
        try:
            response = mam_client.request(MAM_GET_TORRENT_URL.format(torrent_id))
            return response.text
        except Exception as ex:
            print('Error while retrieving MAM data. Will retry: {0}'.format(ex))
            time.sleep(2)
            exception = ex
    raise exception


class MAMTorrent(models.Model):
    info_hash = models.CharField(max_length=40, db_index=True)
    title = models.CharField(max_length=256)
    retrieved = models.DateTimeField()
    category = models.CharField(max_length=32)
    subcategory = models.CharField(max_length=64)
    language = models.CharField(max_length=32)
    isbn = models.CharField(max_length=16)
    cover_url = models.TextField(null=True)
    small_description = models.TextField()
    description = models.TextField()
    html_page = models.TextField()
    torrent_url = models.TextField(null=True)
    torrent_filename = models.TextField(null=True)
    torrent_file = models.BinaryField(null=True)
    torrent_size = models.BigIntegerField()

    def __str__(self):
        return 'MAMTorrent id={0} hash={1}'.format(self.id, self.info_hash)

    def import_mam_data(self, mam_client):
        self.html_page = load_mam_data(mam_client, self.id)
        self.parse_html_page()

    def parse_html_page(self):
        pq = PyQuery(self.html_page)
        main_table = pq('#mainBody > table.coltable')

        def find_row(text):
            for c in list(main_table.find('td:first-child').items()):
                if c.text() == text:
                    return next(list(c.nextAll().items()))

        def find_row_text(text, default=''):
            row = find_row(text)
            if row:
                return row.text()
            return default

        def find_row_html(text, default=''):
            row = find_row(text)
            if row:
                return row.html()
            return default

        self.info_hash = find_row_text('Info hash')
        self.title = pq.find('#mainBody > h1').text()
        self.category, self.subcategory = find_row_text('Type').split(' - ', 1)
        self.language = find_row_text('Language')
        self.cover_url = find_row('Picture:').find('img').attr('src')
        self.small_description = find_row_html('Small Description')
        self.description = find_row_html('Description')
        self.torrent_url = find_row('Download').find('a#dlNormal').attr('href')
        size_string = find_row_text('Size')
        match = re.match('.* \((?P<size>\d+(,\d\d\d)*) bytes\)', size_string)
        self.torrent_size = int(match.group('size').replace(',', ''))

    @staticmethod
    def get_or_create(mam_client, torrent_id):
        try:
            return MAMTorrent.objects.get(id=torrent_id)
        except MAMTorrent.DoesNotExist:
            if not mam_client:
                raise Exception('We do not have the MAMTorrent, but no client was provided.')
            torrent = MAMTorrent(
                id=torrent_id,
                retrieved=timezone.now(),
            )
            torrent.import_mam_data(mam_client)
            if torrent.torrent_url is not None:
                torrent.download_torrent_file(mam_client)
                assert torrent.info_hash == get_info_hash_from_data(torrent.torrent_file)
            torrent.save()
            return torrent

    def download_torrent_file(self, mam_client):
        for i in range(3):
            try:
                self._download_torrent_file(mam_client)
                return
            except Exception as ex:
                exception = ex
                time.sleep(2)
        raise exception

    def _download_torrent_file(self, mam_client):
        if self.torrent_file is not None:
            return
        filename, torrent_file = mam_client.download_torrent(self.torrent_url)
        bencode.bdecode(torrent_file)
        self.torrent_filename = filename
        self.torrent_file = torrent_file


class MAMTransTorrent(TransTorrentBase):
    mam_torrent = models.ForeignKey(MAMTorrent, on_delete=models.CASCADE)

    @property
    def path(self):
        return os.path.join(self.location.path, str(self.mam_torrent_id))

    def __str__(self):
        return 'MAMTransTorrent(torrent_id={0}, mam_id={1}, name={2})'.format(
            self.torrent_id, self.mam_torrent_id, self.torrent_name)


class MAMLoginCache(models.Model):
    cookies = models.TextField()