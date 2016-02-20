import time
import os.path

import bencode
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from pyquery.pyquery import PyQuery

from bibliotik.settings import BIBLIOTIK_GET_TORRENT_URL
from home.models import TransTorrentBase
from what_transcode.utils import get_info_hash_from_data


EBOOK_FORMATS = ['EPUB', 'PDF', 'MOBI', 'AZW3', 'DJVU', 'CBR', 'CHM', 'TXT']
LANGUAGES = ['English', 'Irish', 'German', 'French', 'Spanish', 'Italian', 'Latin', 'Japanese',
             'Danish', 'Swedish', 'Norwegian', 'Dutch', 'Russian', 'Polish', 'Portuguese', 'Greek',
             'Turkish', 'Hungarian', 'Korean', 'Chinese', 'Thai', 'Indonesian', 'Arabic']


def load_bibliotik_data(bibliotik_client, torrent_id):
    exception = None
    for i in xrange(3):
        try:
            response = bibliotik_client.session.get(
                BIBLIOTIK_GET_TORRENT_URL.format(torrent_id), allow_redirects=False)
            if response.status_code != 200:
                raise Exception('Getting bibliotik data returned HTTP {0}'
                                .format(response.status_code))
            return response.text
        except Exception as ex:
            print u'Error while retrieving bibliotik data. Will retry: {0}'.format(ex)
            time.sleep(2)
            exception = ex
    raise exception


class BibliotikTorrent(models.Model):
    info_hash = models.CharField(max_length=40, db_index=True)
    retrieved = models.DateTimeField()
    category = models.CharField(max_length=32)
    format = models.CharField(max_length=16)
    retail = models.BooleanField(default=False)
    pages = models.IntegerField()
    language = models.CharField(max_length=32)
    isbn = models.CharField(max_length=16)
    cover_url = models.TextField()
    tags = models.TextField()
    publisher = models.TextField()
    year = models.IntegerField()
    author = models.TextField()
    title = models.TextField()
    html_page = models.TextField()
    torrent_filename = models.TextField(null=True)
    torrent_file = models.BinaryField(null=True)

    @cached_property
    def publisher_list(self):
        return self.publisher.split(';')

    def __unicode__(self):
        return u'BibliotikTorrent id={0} hash={1}'.format(self.id, self.info_hash)

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
            raise Exception(u'Title should not be empty.')
        self.category = pq('h1#title > img:first-child').attr('title')
        details = pq('p#details_content_info').text().split(', ')
        self.format = details[0]
        details = details[1:]
        if self.category == u'Ebooks':
            assert self.format in EBOOK_FORMATS, u'Unknown eBook format {0}'.format(self.format)
        elif self.category == u'Applications':
            pass
        elif self.category == u'Articles':
            pass
        elif self.category == u'Audiobooks':
            pass
        elif self.category == u'Comics':
            pass
        elif self.category == u'Journals':
            pass
        elif self.category == u'Magazines':
            pass
        else:
            raise Exception(u'Unknown category {0}'.format(self.category))
        if details[0] == u'Retail':
            self.retail = True
            details = details[1:]
        else:
            self.retail = False
        if details[0].endswith(u'pages'):
            self.pages = int(details[0][:-len(u'pages') - 1])
            details = details[1:]
        else:
            self.pages = 0
        if details[0] == u'Unabridged' or details[0] == u'Abridged':
            details = details[1:]
        if details[0].split(' ')[0] in LANGUAGES:
            parts = details[0].split(' ')
            details = details[1:]
            self.language = parts[0]
            parts = parts[1:]
            if len(parts):
                assert parts[0][0] == '(' and parts[0][-1] == ')', u'Unknown string after language'
                self.isbn = parts[0][1:-1]
                parts = parts[1:]
            else:
                self.isbn = ''
        else:
            self.language = ''
        assert len(details) == 0, u'All details must be parsed: {0}'.format(', '.join(details))
        self.cover_url = pq('div#sidebar > a[rel="lightbox"] > img').attr('src') or ''
        self.tags = ', '.join(i.text() for i in pq('span.taglist > a').items())
        publisher_year = pq('p#published').text()
        if publisher_year:
            assert publisher_year.startswith('Published '), \
                "Publisher doesn't start with Published"
            publisher_year = publisher_year[len('Published '):]
            if publisher_year.startswith('by '):
                publisher_year = publisher_year[len('by '):]
                self.publisher = ';'.join(i.text() for i in pq('p#published > a').items())
                assert self.publisher, 'Publisher can not be empty'
                publisher_mod = ' , '.join(i.text() for i in pq('p#published > a').items())
                assert publisher_year.startswith(publisher_mod), \
                    'publisher_year does not start with self.publisher'
                publisher_year = publisher_year[len(publisher_mod) + 1:]
            else:
                self.publisher = ''
            if publisher_year:
                assert publisher_year.startswith('in '), 'Invalid publisher_year'
                publisher_year = publisher_year[len('in '):]
                self.year = int(publisher_year)
            else:
                self.year = 0

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


class BibliotikFulltext(models.Model):
    info = models.TextField()
    more_info = models.TextField()

    def update(self, bibliotik_torrent):
        info = u'{0} - {1}'.format(bibliotik_torrent.author, bibliotik_torrent.title)
        more_info = ' '.join([
            ', '.join(bibliotik_torrent.publisher_list),
            bibliotik_torrent.isbn,
            str(bibliotik_torrent.year),
            bibliotik_torrent.format,
            bibliotik_torrent.tags
        ])
        if self.info != info or self.more_info != more_info:
            self.info = info
            self.more_info = more_info
            self.save()
