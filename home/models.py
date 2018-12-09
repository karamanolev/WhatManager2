import base64
import hashlib
import os
import pickle
import re
import socket
import ujson
from itertools import count
from time import sleep

import mutagen
import requests
import transmissionrpc
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.functional import cached_property

from WhatManager2 import settings
from WhatManager2.settings import FREELEECH_EMAIL_TO, WHAT_CD_DOMAIN, FREELEECH_HOSTNAME, \
    FREELEECH_EMAIL_FROM
from WhatManager2.throttling import Throttler
from WhatManager2.utils import match_properties, copy_properties, norm_t_torrent, html_unescape, \
    get_artists
from home.info_holder import InfoHolder
from what_meta.models import WhatTorrentGroup


class TorrentAlreadyAddedException(Exception):
    pass


class ReplicaSet(models.Model):
    ZONE_WHAT = 'redacted.ch'
    ZONE_BIBLIOTIK = 'bibliotik.me'
    ZONE_MYANONAMOUSE = 'myanonamouse.net'

    zone = models.CharField(max_length=32)
    name = models.TextField()

    def __str__(self):
        return 'ReplicaSet({0}, {1})'.format(self.zone, self.name)

    @property
    def is_master(self):
        return self.name == 'master'

    @property
    def torrent_count(self):
        return sum(i.torrent_count for i in self.transinstance_set.all())

    @property
    def torrents_size(self):
        return sum(i.torrents_size for i in self.transinstance_set.all())

    def get_preferred_instance(self):
        return sorted(self.transinstance_set.all(), key=lambda x: x.torrent_count)[0]

    @classmethod
    def get_what_master(cls):
        return cls.objects.get(zone=cls.ZONE_WHAT, name='master')

    @classmethod
    def get_bibliotik_master(cls):
        return cls.objects.get(zone=cls.ZONE_BIBLIOTIK, name='master')

    @classmethod
    def get_myanonamouse_master(cls):
        return cls.objects.get(zone=cls.ZONE_MYANONAMOUSE, name='master')


class DownloadLocation(models.Model):
    zone = models.CharField(max_length=32)
    path = models.TextField()
    preferred = models.BooleanField(default=False)

    def __str__(self):
        return 'DownloadLocation({0}, {1}{2})'.format(
            self.zone, self.path, ', preferred' if self.preferred else '')

    @cached_property
    def disk_space(self):
        stat = os.statvfs(self.path)
        return {
            'free': stat.f_bfree * stat.f_bsize,
            'used': (stat.f_blocks - stat.f_bfree) * stat.f_bsize,
            'total': stat.f_blocks * stat.f_bsize
        }

    @cached_property
    def free_space_percent(self):
        return float(self.disk_space['free']) / self.disk_space['total']

    @classmethod
    def get_what_preferred(cls):
        return DownloadLocation.objects.get(
            zone=ReplicaSet.ZONE_WHAT,
            preferred=True,
        )

    @classmethod
    def get_bibliotik_preferred(cls):
        return DownloadLocation.objects.get(
            zone=ReplicaSet.ZONE_BIBLIOTIK,
            preferred=True,
        )

    @classmethod
    def get_myanonamouse_preferred(cls):
        return DownloadLocation.objects.get(
            zone=ReplicaSet.ZONE_MYANONAMOUSE,
            preferred=True,
        )

    @cached_property
    def torrent_count(self):
        replica_sets = ReplicaSet.objects.filter(name='master')
        instances = TransInstance.objects.filter(replica_set__in=replica_sets)
        return (
            self.transtorrent_set.filter(instance__in=instances).count() +
            self.bibliotiktranstorrent_set.filter(instance__in=instances).count()
        )

    @classmethod
    def get_by_full_path(cls, full_path):
        for d in DownloadLocation.objects.all():
            if full_path.startswith(d.path):
                return d
        return None


class TransInstance(models.Model):
    class Meta:
        permissions = (
            ('view_transinstance_stats', 'Can view current Transmission stats.'),
            ('run_checks', 'Can run the validity checks.'),
        )

    replica_set = models.ForeignKey(ReplicaSet, on_delete=models.CASCADE)
    name = models.TextField()
    host = models.TextField()
    port = models.IntegerField()
    peer_port = models.IntegerField()
    username = models.TextField()
    password = models.TextField()

    def __str__(self):
        return 'TransInstance {0}({1}@{2}:{3})'.format(self.name, self.username,
                                                        self.host, self.port)

    def full_description(self):
        return 'TransInstance {0}(replica_set={1}, host={2}, rpc_port={3}, ' \
               'peer_port={4}, username={5}, password={6})' \
            .format(self.name, self.replica_set, self.host, self.port, self.peer_port,
                    self.username, self.password)

    @property
    def client(self):
        if not hasattr(self, '_client'):
            self._client = transmissionrpc.Client(address=self.host, port=self.port,
                                                  user=self.username, password=self.password)
        return self._client

    @property
    def torrent_count(self):
        if self.replica_set.zone == ReplicaSet.ZONE_WHAT:
            return self.transtorrent_set.count()
        elif self.replica_set.zone == ReplicaSet.ZONE_BIBLIOTIK:
            return self.bibliotiktranstorrent_set.count()

    @property
    def torrents_size(self):
        if self.replica_set.zone == ReplicaSet.ZONE_WHAT:
            return self.transtorrent_set.aggregate(Sum('torrent_size'))['torrent_size__sum']
        elif self.replica_set.zone == ReplicaSet.ZONE_BIBLIOTIK:
            return self.bibliotiktranstorrent_set.aggregate(
                Sum('torrent_size'))['torrent_size__sum']

    def get_t_torrents(self, arguments):
        torrents = []
        locations = DownloadLocation.objects.filter(zone=self.replica_set.zone)
        if 'downloadDir' not in arguments:
            arguments.append('downloadDir')
        for t in self.client.get_torrents(arguments=arguments):
            if any([l for l in locations if t.downloadDir.startswith(l.path)]):
                norm_t_torrent(t)
                torrents.append(t)
        return torrents

    def get_t_torrents_by_hash(self, arguments):
        torrents = {}
        for t in self.get_t_torrents(arguments):
            torrents[t.hashString] = t
        return torrents

    def get_m_torrents_by_hash(self):
        torrents = {}
        for t in self.transtorrent_set.all():
            existing = torrents.get(t.info_hash)
            if existing and t.what_torrent_id == existing.what_torrent_id:
                t.delete()
                continue
            torrents[t.info_hash] = t
        return torrents

    def get_b_torrents_by_hash(self):
        torrents = {}
        for t in self.bibliotiktranstorrent_set.all():
            existing = torrents.get(t.info_hash)
            if existing and t.bibliotik_torrent_id == existing.bibliotik_torrent_id:
                t.delete()
                continue
            torrents[t.info_hash] = t
        return torrents

    def get_mam_torrents_by_hash(self):
        torrents = {}
        for t in self.mamtranstorrent_set.all():
            existing = torrents.get(t.info_hash)
            if existing and t.mam_torrent_id == existing.mam_torrent_id:
                t.delete()
                continue
            torrents[t.info_hash] = t
        return torrents


class WhatFulltext(models.Model):
    info = models.TextField()
    more_info = models.TextField()

    def get_info(self, what_torrent):
        info = ujson.loads(what_torrent.info)

        info_text = []
        info_text.append(str(info['group']['id']))
        info_text.append(info['group']['recordLabel'])
        info_text.append(info['group']['name'])
        info_text.append(info['group']['catalogueNumber'])
        if info['group']['musicInfo']:
            for type, artists in list(info['group']['musicInfo'].items()):
                if artists:
                    artist_names = [a['name'] for a in artists]
                    info_text.append(', '.join(artist_names))
        info_text.append(str(info['group']['year']))

        info_text.append(str(info['torrent']['id']))
        info_text.append(str(info['torrent']['remasterYear']))
        info_text.append(info['torrent']['filePath'])
        info_text.append(info['torrent']['remasterCatalogueNumber'])
        info_text.append(info['torrent']['remasterRecordLabel'])
        info_text.append(info['torrent']['remasterTitle'])

        info_text = '\r\n'.join(info_text)
        info_text = html_unescape(info_text)
        return info_text

    def match(self, what_torrent):
        return (
            self.get_info(what_torrent) == self.info and
            what_torrent.info == self.more_info
        )

    def update(self, what_torrent):
        self.info = self.get_info(what_torrent)
        self.more_info = what_torrent.info
        self.save()

    def __str__(self):
        return 'WhatFulltext id={0}'.format(self.id)


class WhatTorrent(models.Model, InfoHolder):
    class Meta:
        permissions = (
            ('download_whattorrent', 'Can download and play torrents.'),
        )

    info_hash = models.CharField(max_length=40, db_index=True)
    torrent_file = models.TextField()
    torrent_file_name = models.TextField()
    retrieved = models.DateTimeField(db_index=True)
    info = models.TextField()
    tags = models.TextField()
    added_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    torrent_group = models.ForeignKey('what_meta.WhatTorrentGroup', null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            try:
                if int(self.info_category_id) == 1:
                    self.torrent_group = WhatTorrentGroup.update_if_newer(
                        self.info_loads['group']['id'], self.retrieved, self.info_loads['group'])
            except Exception:
                pass
            super(WhatTorrent, self).save(*args, **kwargs)
        try:
            what_fulltext = WhatFulltext.objects.get(id=self.id)
            if not what_fulltext.match(self):
                what_fulltext.update(self)
        except WhatFulltext.DoesNotExist:
            what_fulltext = WhatFulltext(id=self.id)
            what_fulltext.update(self)

    def delete(self, *args, **kwargs):
        try:
            WhatFulltext.objects.get(id=self.id).delete()
        except WhatFulltext.DoesNotExist:
            pass
        super(WhatTorrent, self).delete(*args, **kwargs)

    def __str__(self):
        return 'WhatTorrent id={0} hash={1}'.format(self.id, self.info_hash)

    @cached_property
    def master_trans_torrent(self):
        torrents = list(TransTorrent.objects.filter(
            what_torrent=self,
            instance__in=ReplicaSet.get_what_master().transinstance_set.all()
        ))
        if len(torrents):
            return torrents[0]
        return None

    @cached_property
    def joined_artists(self):
        return get_artists(self.info_loads['group'])

    @property
    def torrent_file_binary(self):
        return base64.b64decode(self.torrent_file)

    @cached_property
    def info_loads(self):
        return ujson.loads(self.info)

    @staticmethod
    def get_or_none(request, info_hash=None, what_id=None):
        if info_hash and what_id:
            raise Exception('Specify one.')
        if not info_hash and not what_id:
            raise Exception('Specify one.')
        try:
            if info_hash:
                return WhatTorrent.objects.get(info_hash=info_hash)
            elif what_id:
                return WhatTorrent.objects.get(id=what_id)
        except WhatTorrent.DoesNotExist:
            return None

    @staticmethod
    def is_downloaded(request, info_hash=None, what_id=None):
        w_torrent = WhatTorrent.get_or_none(request, info_hash, what_id)
        if w_torrent and w_torrent.transtorrent_set.count() > 0:
            return True
        return False

    @staticmethod
    def get_or_create(request, info_hash=None, what_id=None):
        if info_hash and what_id:
            raise Exception('Specify either an infohash OR an ID, not both.')
        if not info_hash and not what_id:
            raise Exception('You must specify an infohash or an ID.')

        try:
            if info_hash:
                if len(info_hash) != 40:
                    raise Exception('Invalid info hash.')
                return WhatTorrent.objects.get(info_hash=info_hash)
            else:
                return WhatTorrent.objects.get(id=what_id)
        except WhatTorrent.DoesNotExist:
            what = get_what_client(request)

            if info_hash:
                data = what.request('torrent', hash=info_hash)['response']
            else:
                data = what.request('torrent', id=what_id)['response']

            filename, torrent = what.get_torrent(data['torrent']['id'])
            w_torrent = WhatTorrent(
                id=int(data['torrent']['id']),
                info_hash=data['torrent']['infoHash'],
                torrent_file=base64.b64encode(torrent).decode('utf-8'),
                torrent_file_name=filename,
                retrieved=timezone.now(),
                info=ujson.dumps(data)
            )
            w_torrent.save()
            return w_torrent


class TransTorrentBase(models.Model):
    class Meta:
        abstract = True

    sync_t_arguments = [
        'id', 'name', 'hashString', 'totalSize', 'uploadedEver', 'percentDone', 'addedDate',
        'error', 'errorString'
    ]
    sync_t_props = (
        ('torrent_id', 'id'),
        ('torrent_name', 'name'),
        ('torrent_size', 'totalSize'),
        ('torrent_uploaded', 'uploadedEver'),
        ('torrent_done', 'percentDone'),
        ('torrent_date_added', 'date_added_tz'),
        ('torrent_error', 'error'),
        ('torrent_error_string', 'errorString'),
    )

    instance = models.ForeignKey(TransInstance, on_delete=models.CASCADE)
    location = models.ForeignKey(DownloadLocation, on_delete=models.CASCADE)

    info_hash = models.CharField(max_length=40)
    torrent_id = models.IntegerField(null=True)
    torrent_name = models.TextField(null=True)
    torrent_size = models.BigIntegerField(null=True)
    torrent_uploaded = models.BigIntegerField(null=True)
    torrent_done = models.FloatField(null=True)
    torrent_date_added = models.DateTimeField(null=True)
    torrent_error = models.IntegerField(null=True)
    torrent_error_string = models.TextField(null=True)

    def sync_t_torrent(self, t_torrent=None):
        if t_torrent is None:
            t_torrent = self.instance.client.get_torrent(
                self.torrent_id, arguments=TransTorrentBase.sync_t_arguments)
            norm_t_torrent(t_torrent)

        if not match_properties(self, t_torrent, TransTorrentBase.sync_t_props):
            copy_properties(self, t_torrent, TransTorrentBase.sync_t_props)
            self.save()


class TransTorrent(TransTorrentBase):
    what_torrent = models.ForeignKey(WhatTorrent, on_delete=models.CASCADE)

    @property
    def path(self):
        return os.path.join(self.location.path, str(self.what_torrent.id))

    def sync_files(self):
        if os.path.exists(self.path):
            files = [f for f in os.listdir(self.path)]
        else:
            os.mkdir(self.path, 0o777)
            os.chmod(self.path, 0o777)
            files = []

        files_added = []
        if not any('.torrent' in f for f in files):
            files_added.append('torrent')
            torrent_path = os.path.join(self.path, self.what_torrent.torrent_file_name)
            with open(torrent_path, 'wb') as file:
                file.write(self.what_torrent.torrent_file_binary)
            os.chmod(torrent_path, 0o777)
        if not any('ReleaseInfo2.txt' == f for f in files):
            files_added.append('ReleaseInfo2.txt')
            release_info_path = os.path.join(self.path, 'ReleaseInfo2.txt')
            with open(release_info_path, 'w') as file:
                file.write(self.what_torrent.info)
            os.chmod(os.path.join(release_info_path), 0o777)
        if files_added:
            LogEntry.add(None, 'info', 'Added files {0} to {1}'
                         .format(', '.join(files_added), self))

    def __str__(self):
        return 'TransTorrent(torrent_id={0}, what_id={1}, name={2})'.format(
            self.torrent_id, self.what_torrent_id, self.torrent_name)


class LogEntry(models.Model):
    user = models.ForeignKey(User, null=True, related_name='wm_logentry', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.TextField()
    message = models.TextField()
    traceback = models.TextField(null=True)

    @staticmethod
    def add(user, log_type, message, traceback=None):
        entry = LogEntry(user=user, type=log_type, message=message, traceback=traceback)
        entry.save()


class WhatFileMetadataCache(models.Model):
    what_torrent = models.ForeignKey(WhatTorrent, on_delete=models.CASCADE)
    filename_sha256 = models.CharField(max_length=64, primary_key=True)
    filename = models.CharField(max_length=500)
    file_mtime = models.IntegerField()
    metadata_pickle = models.BinaryField()
    artists = models.CharField(max_length=200)
    album = models.CharField(max_length=200)
    title = models.CharField(max_length=200, db_index=True)
    duration = models.FloatField()

    @cached_property
    def metadata(self):
        return pickle.loads(self.metadata_pickle)

    @cached_property
    def easy(self):
        data = {
            'artist': '',
            'album': '',
            'title': '',
            'duration': self.metadata.info.length,
        }
        if self.metadata.get('albumartist') and self.metadata['albumartist'][0]:
            data['artist'] = ', '.join(self.metadata['albumartist'])
        if self.metadata.get('artist') and self.metadata['artist'][0]:
            data['artist'] = ', '.join(self.metadata['artist'])
        if self.metadata.get('performer') and self.metadata['performer'][0]:
            data['artist'] = ', '.join(self.metadata['performer'])
        if 'album' in self.metadata and self.metadata['album']:
            data['album'] = ', '.join(self.metadata['album'])
        if 'title' in self.metadata and self.metadata['title']:
            data['title'] = ', '.join(self.metadata['title'])
        return data

    def fill(self, filename, file_mtime):
        metadata = mutagen.File(filename, easy=True)
        if hasattr(metadata, 'pictures'):
            for p in metadata.pictures:
                p.data = None
        if hasattr(metadata, 'tags'):
            if hasattr(metadata.tags, '_EasyID3__id3'):
                metadata.tags._EasyID3__id3.delall('APIC')
        self.file_mtime = file_mtime
        try:
            self.metadata_pickle = pickle.dumps(metadata)
        except:
            self.metadata_pickle = pickle.dumps(metadata, pickle.HIGHEST_PROTOCOL)
            pass
        self.artists = self.easy['artist'][:200]
        self.album = self.easy['album'][:200]
        self.title = self.easy['title'][:200]
        self.duration = self.easy['duration']

    @classmethod
    def get_metadata_batch(cls, what_torrent, trans_torrent, force_update):
        torrent_path = trans_torrent.path
        cache_lines = list(what_torrent.whatfilemetadatacache_set.all())
        if len(cache_lines) and not force_update:
            for cache_line in cache_lines:
                cache_line.path = os.path.join(torrent_path, cache_line.filename)
            return sorted(cache_lines, key=lambda c: c.path)

        cache_lines = {c.filename_sha256: c for c in cache_lines}

        abs_rel_filenames = []
        for dirpath, dirnames, filenames in os.walk(torrent_path):
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in ['.flac', '.mp3']:
                    abs_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(abs_path, torrent_path)
                    abs_rel_filenames.append((abs_path, rel_path))
        abs_rel_filenames.sort(key=lambda f: f[1])

        filename_hashes = {f[0]: hashlib.sha256(f[1].encode('utf-8')).hexdigest() for f in 
                           abs_rel_filenames}
        hash_set = set(filename_hashes.values())
        old_cache_lines = []
        for cache_line in cache_lines.values():
            if cache_line.filename_sha256 not in hash_set:
                old_cache_lines.append(cache_line)
        dirty_cache_lines = []

        result = []
        for abs_path, rel_path in abs_rel_filenames:
            try:
                file_mtime = os.path.getmtime(abs_path)
                cache = cache_lines.get(filename_hashes[abs_path])
                if cache is None:
                    cache = WhatFileMetadataCache(
                        what_torrent=what_torrent,
                        filename_sha256=filename_hashes[abs_path],
                        filename=rel_path[:400],
                        file_mtime=0
                    )
                cache.path = abs_path
                if abs(file_mtime - cache.file_mtime) <= 1:
                    result.append(cache)
                    continue
                cache.fill(abs_path, file_mtime)
                dirty_cache_lines.append(cache)
                result.append(cache)
            except Exception as ex:
                print('Failed:', abs_path, ex)
        if old_cache_lines or dirty_cache_lines:
            with transaction.atomic():
                for cache_line in old_cache_lines:
                    cache_line.delete()
                for cache_line in dirty_cache_lines:
                    cache_line.save()
        return result


class WhatLoginCache(models.Model):
    cookies = models.TextField()
    authkey = models.TextField()
    passkey = models.TextField()


headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept-Charset': 'utf-8',
    'User-Agent': 'whatapi [isaaczafuta]'
}


class LoginException(Exception):
    pass


class RequestException(Exception):
    def __init__(self, message=None, response=None):
        super(Exception, self).__init__(message)
        self.response = response


class BadIdException(RequestException):
    def __init__(self, response=None):
        super(BadIdException, self).__init__('Bad ID Parameter.', response)


class RateLimitExceededException(RequestException):
    def __init__(self, response=None):
        super(RateLimitExceededException, self).__init__('Rate limit exceeded.', response)


def send_freeleech_email(message):
    send_mail('Freeleech', message, FREELEECH_EMAIL_FROM, [FREELEECH_EMAIL_TO])


class CustomWhatAPI:
    def __init__(self, username=None, password=None, throttle=False):
        self.session = requests.Session()
        self.session.headers = headers
        self.authkey = None
        self.passkey = None
        self.username = username
        self.password = password
        self.throttle = throttle
        self.throttler = Throttler(5, 10)
        self._login()

    def _login(self):
        try:
            login_cache = WhatLoginCache.objects.get()
            self.session.cookies.update(login_cache.cookies)
            self.authkey = login_cache.authkey
            self.passkey = login_cache.passkey
            self.request('index')
        except Exception:
            '''Logs in user and gets authkey from server'''
            loginpage = 'https://{0}/login.php'.format(WHAT_CD_DOMAIN)
            data = {
                'username': self.username,
                'password': self.password,
                'keeplogged': 1,
                'login': 'Login',
            }
            r = self.session.post(loginpage, data=data, allow_redirects=False)
            if r.status_code != 302:
                if '<form class="auth_form" name="2fa" id="2fa"' in r.text:
                    raise LoginException("2FA is enabled on your account, unable to login.")
                else:
                    raise LoginException("Unsuccessful login attempt.")
            accountinfo = self.request("index")
            self.authkey = accountinfo["response"]["authkey"]
            self.passkey = accountinfo["response"]["passkey"]
            for cache in WhatLoginCache.objects.all():
                cache.delete()
            login_cache = WhatLoginCache(
                cookies=self.session.cookies,
                authkey=self.authkey,
                passkey=self.passkey
            )
            login_cache.save()

    def request(self, action, **kwargs):
        '''Makes an AJAX request at a given action page'''
        ajaxpage = 'https://{0}/ajax.php'.format(WHAT_CD_DOMAIN)
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)

        if self.throttle:
            self.throttler.throttle_request()
        r = self.session.get(ajaxpage, params=params, allow_redirects=False)
        try:
            json_response = r.json()
            if json_response["status"] != "success":
                if json_response['error'] == 'bad id parameter':
                    raise BadIdException(json_response)
                elif json_response['error'] == 'rate limit exceeded':
                    raise RateLimitExceededException(json_response)
                raise RequestException(
                    message=json_response['error'] if 'error' in json_response else json_response,
                    response=json_response)
            return json_response
        except ValueError:
            if action == 'torrentlog' and r.content == 'no payload data (empty result set)':
                return {'status': 'success', 'response': []}
            raise RequestException()

    def get_torrent(self, torrent_id):
        '''Downloads the torrent at torrent_id using the authkey and passkey'''
        torrentpage = 'https://{0}/torrents.php'.format(WHAT_CD_DOMAIN)
        params = {'action': 'download', 'id': torrent_id}
        if self.authkey:
            params['authkey'] = self.authkey
            params['torrent_pass'] = self.passkey
        r = self.session.get(torrentpage, params=params, allow_redirects=False)
        if r.status_code == 200 and 'application/x-bittorrent' in r.headers['content-type']:
            filename = re.search('filename="(.*)"', r.headers['content-disposition']).group(1)
            return filename, r.content
        return None

    def get_free_torrents(self):
        # Start form 1 up
        for page in count(1):
            response = self.request('browse', freetorrent=1, page=page)['response']
            if response['pages'] > 20 and socket.gethostname() == FREELEECH_HOSTNAME:
                send_freeleech_email('Site-wide freeleech.')
                raise Exception('More than 20 pages of free torrents. Site-wide freeleech?')
            for result in response['results']:
                yield result
            if response['currentPage'] == response['pages']:
                break
            sleep(2)

    def get_free_torrent_ids(self):
        for free_group in self.get_free_torrents():
            if 'torrents' in free_group:
                for torrent in free_group['torrents']:
                    if torrent['isFreeleech']:
                        yield int(torrent['torrentId']), free_group, torrent
            else:
                if free_group['isFreeleech']:
                    yield int(free_group['torrentId']), free_group, free_group


def get_what_client(request, throttle=False):
    if not hasattr(request, 'what_client'):
        request.what_client = None
        for i in range(3):
            try:
                request.what_client = CustomWhatAPI(username=settings.WHAT_USERNAME,
                                                    password=settings.WHAT_PASSWORD,
                                                    throttle=throttle)
                break
            except RequestException as ex:
                pass
        if request.what_client is None:
            raise ex
    return request.what_client
