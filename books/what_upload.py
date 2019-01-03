import os
import os.path
import shutil

from WhatManager2 import manage_torrent
from WhatManager2.settings import WHAT_UPLOAD_URL
from home.models import get_what_client, DownloadLocation, ReplicaSet, WhatTorrent
from what_transcode.utils import extract_upload_errors, safe_retrieve_new_torrent, \
    get_info_hash_from_data


def get_what_tags(book_upload):
    tag_list = book_upload.tag_list
    # Retail
    if book_upload.retail:
        tag_list.append('retail')
    # Format
    tag_list.append(book_upload.format.lower())
    # Rest of tags
    tag_list = [s.strip().replace(' ', '.') for s in tag_list]
    return ', '.join(tag_list)


def get_what_desc(book_upload):
    desc = list()
    desc.append('Publisher: {0}'.format(book_upload.publisher))
    if book_upload.year and book_upload.year != '0':
        desc.append('Publication Year: {0}'.format(book_upload.year))
    if book_upload.isbn:
        desc.append('ISBN: {0}'.format(book_upload.isbn))
    if book_upload.pages and book_upload.pages != '0':
        desc.append('Pages: {0}'.format(book_upload.pages))
    desc.append('')
    desc.append(book_upload.description)
    return '\n'.join(desc)


def move_to_dest_add(request, book_upload):
    location = DownloadLocation.get_what_preferred()
    dest_path = os.path.join(location.path, str(book_upload.what_torrent_id))
    book_path = os.path.join(dest_path, book_upload.target_filename)
    if not os.path.exists(dest_path):
        os.mkdir(dest_path)
    os.chmod(dest_path, 0o777)
    shutil.copyfile(
        book_upload.book_data.storage.path(book_upload.book_data),
        book_path
    )
    os.chmod(book_path, 0o777)
    manage_torrent.add_torrent(request, ReplicaSet.get_what_master().get_preferred_instance(),
                               location, book_upload.what_torrent_id)


def upload_to_what(request, book_upload):
    book_upload.full_clean()
    if not book_upload.what_torrent_file:
        raise Exception('what_torrent is no')
    if not book_upload.cover_url:
        raise Exception('cover_url is no')

    print('Sending request for upload to what.cd')

    what = get_what_client(request)

    payload_files = dict()
    payload_files['file_input'] = ('torrent.torrent', book_upload.what_torrent_file)

    payload = dict()
    payload['submit'] = 'true'
    payload['auth'] = what.authkey
    payload['type'] = '2'
    payload['title'] = book_upload.author + ' - ' + book_upload.title
    payload['tags'] = get_what_tags(book_upload)
    payload['image'] = book_upload.cover_url
    payload['desc'] = get_what_desc(book_upload)

    old_content_type = what.session.headers['Content-type']
    upload_exception = None
    try:
        del what.session.headers['Content-type']
        response = what.session.post(WHAT_UPLOAD_URL, data=payload, files=payload_files)
        if response.url == WHAT_UPLOAD_URL:
            try:
                errors = extract_upload_errors(response.text)
            except Exception:
                errors = ''
            exception = Exception('Error uploading data to what.cd. Errors: {0}'
                                  .format('; '.join(errors)))
            exception.response_text = response.text
            raise exception
    except Exception as ex:
        upload_exception = ex
    finally:
        what.session.headers['Content-type'] = old_content_type

    try:
        new_torrent = safe_retrieve_new_torrent(
            what, get_info_hash_from_data(book_upload.what_torrent_file))
        book_upload.what_torrent = WhatTorrent.get_or_create(
            request, what_id=new_torrent['torrent']['id'])
        book_upload.save()
    except Exception as ex:
        if upload_exception:
            raise upload_exception
        raise ex

    move_to_dest_add(request, book_upload)
    return book_upload.what_torrent
