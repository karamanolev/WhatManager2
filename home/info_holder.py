import os

from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from WhatManager2.utils import html_unescape


WHAT_RELEASE_TYPES = (
    (1, 'Album'),
    (3, 'Soundtrack'),
    (5, 'EP'),
    (6, 'Anthology'),
    (7, 'Compilation'),
    (8, 'DJ Mix'),
    (9, 'Single'),
    (11, 'Live album'),
    (13, 'Remix'),
    (14, 'Bootleg'),
    (15, 'Interview'),
    (16, 'Mixtape'),
    (21, 'Unknown'),
    (22, 'Concert Recording'),
    (23, 'Demo'),
)


def safe_return(func):
    def wrapped(*args, **kwargs):
        res = func(*args, **kwargs)
        if res is None:
            return None
        return mark_safe(res)

    return wrapped


def get_release_type_name(id):
    id = int(id)
    for type in WHAT_RELEASE_TYPES:
        if type[0] == id:
            return type[1]
    return None


def get_release_type_id(name):
    name = str(name)
    for type in WHAT_RELEASE_TYPES:
        if type[1] == name:
            return type[0]
    return None


def parse_file(file):
    parts = file.replace('}}}', '').split('{{{')
    return {
        'name': html_unescape(parts[0]),
        'size': int(parts[1])
    }


IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.tif']


def is_image_file(file):
    ext = os.path.splitext(file)[1]
    return any(e == ext for e in IMAGE_EXTS)


def parse_file_list(file_list):
    files = file_list.split('|||')
    return sorted([parse_file(f) for f in files], key=lambda i: i['name'])


class InfoHolder(object):
    @cached_property
    @safe_return
    def info_artist(self):
        artists = self.info_loads['group']['musicInfo']['artists']
        if len(artists) == 0:
            composers = self.info_loads['group']['musicInfo']['composers']
            if len(composers) == 0:
                return ''
            elif len(composers) <= 3:
                return ', '.join(a['name'] for a in composers)
            else:
                return 'Various Composers'
        elif len(artists) <= 3:
            return ', '.join(a['name'] for a in artists)
        else:
            return 'Various Artists'

    @cached_property
    def info_remastered(self):
        return self.info_loads['torrent']['remastered']

    @cached_property
    def info_release_type_name(self):
        return get_release_type_name(self.info_loads['group']['releaseType'])

    @cached_property
    def info_year(self):
        remaster_year = self.info_loads['torrent']['remasterYear']
        year = self.info_loads['group']['year']
        if self.info_remastered and remaster_year != year:
            return '{0} ({1})'.format(remaster_year, year)
        return year

    @cached_property
    @safe_return
    def info_title(self):
        return self.info_loads['group']['name']

    @cached_property
    @safe_return
    def info_media(self):
        return self.info_loads['torrent']['media']

    @cached_property
    @safe_return
    def info_format(self):
        return self.info_loads['torrent']['format']

    @cached_property
    @safe_return
    def info_encoding(self):
        return self.info_loads['torrent']['encoding']

    @cached_property
    @safe_return
    def info_label(self):
        remaster_label = self.info_loads['torrent']['remasterRecordLabel']
        label = self.info_loads['group']['recordLabel']
        return remaster_label if self.info_remastered else label

    @cached_property
    @safe_return
    def info_catno(self):
        remaster_catno = self.info_loads['torrent']['remasterCatalogueNumber']
        catno = self.info_loads['group']['catalogueNumber']
        return remaster_catno if self.info_remastered else catno

    @cached_property
    @safe_return
    def info_remaster_title(self):
        if self.info_remastered:
            return self.info_loads['torrent']['remasterTitle']
        return None

    @cached_property
    def info_files(self):
        return parse_file_list(self.info_loads['torrent']['fileList'])

    @cached_property
    def info_image_files(self):
        return [f for f in self.info_files if is_image_file(f['name'])]

    @cached_property
    def info_has_artwork(self):
        return len(self.info_image_files) >= 2

    @cached_property
    def info_size(self):
        return self.info_loads['torrent']['size']

    @cached_property
    def info_category_id(self):
        return self.info_loads['group']['categoryId']
