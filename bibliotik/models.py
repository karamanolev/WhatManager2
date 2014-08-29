import time
import os.path

import bencode
from django.db import models
from django.utils import timezone
from pyquery.pyquery import PyQuery

from bibliotik.settings import BIBLIOTIK_GET_TORRENT_URL
from home.models import TransTorrentBase
from what_transcode.utils import get_info_hash_from_data


def load_bibliotik_data(bibliotik_client, torrent_id):
    exception = None
    for i in xrange(3):
        try:
            response = bibliotik_client.session.get(
                BIBLIOTIK_GET_TORRENT_URL.format(torrent_id), allow_redirects=False)
            if response.status_code != 200:
                raise Exception('Getting bibliotik data returned HTTP {0}'.format(response.status_code))
            return response.text
        except Exception as ex:
            print u'Error while retrieving bibliotik data. Will retry: {0}'.format(ex)
            time.sleep(2)
            exception = ex
    raise exception


class BibliotikTorrent(models.Model):
    info_hash = models.TextField()
    retrieved = models.DateTimeField()
    author = models.TextField()
    title = models.TextField()
    html_page = models.TextField()
    torrent_filename = models.TextField(null=True)
    torrent_file = models.BinaryField(null=True)

    def import_bibliotik_data(self, bibliotik_client):
        self.html_page = load_bibliotik_data(bibliotik_client, self.id)
        self.parse_html_page()

    def parse_html_page(self):
        pq = PyQuery(self.html_page)
        authors = []
        for author in pq('p#creatorlist a').items():
            authors.append(author.text())
        self.author = ', '.join(authors)
        self.title = pq('h1#title').text()
        if not self.title:
            raise Exception('Title should not be empty.')

    @staticmethod
    def get_or_create(bibliotik_client, torrent_id):
        try:
            return BibliotikTorrent.objects.get(id=torrent_id)
        except BibliotikTorrent.DoesNotExist:
            if not bibliotik_client:
                raise Exception('We do not have the BibliotikTorrent, but no client was provided.')
            torrent = BibliotikTorrent(
                id=torrent_id,
                retrieved=timezone.now(),
            )
            torrent.import_bibliotik_data(bibliotik_client)
            torrent.download_torrent_file(bibliotik_client)
            torrent.info_hash = get_info_hash_from_data(torrent.torrent_file)
            torrent.save()
            return torrent

    def download_torrent_file(self, bibliotik_client):
        for i in xrange(3):
            try:
                self._download_torrent_file(bibliotik_client)
                return
            except Exception as ex:
                exception = ex
                time.sleep(2)
        raise exception

    def _download_torrent_file(self, bibliotik_client):
        if self.torrent_file is not None:
            return
        filename, torrent_file = bibliotik_client.download_torrent(self.id)
        bencode.bdecode(torrent_file)
        self.torrent_filename = filename
        self.torrent_file = torrent_file


class BibliotikTransTorrent(TransTorrentBase):
    bibliotik_torrent = models.ForeignKey(BibliotikTorrent)

    @property
    def path(self):
        return os.path.join(self.location.path, unicode(self.bibliotik_torrent.id))

    def __unicode__(self):
        return u'BibliotikTransTorrent(torrent_id={0}, bibliotik_id={1}, name={2})'.format(
            self.torrent_id, self.bibliotik_torrent_id, self.torrent_name)
