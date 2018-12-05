#! /usr/bin/env python
import argparse
import hashlib
import itertools
import os

import bencode

parser = argparse.ArgumentParser(
    description='Check the integrity of torrent downloads.')
parser.add_argument('directory', help='download directory')
parser.add_argument('torrent', nargs='*', help='torrent file')
parser.add_argument(
    '--delete',
    action='store_true',
    help='delete files that are not found in the torrent file; '
    'do nothing if the torrent file has only a single file')
parser.add_argument(
    '--list-delete',
    action='store_true',
    help='list the files that would be deleted if --delete was set')
parser.add_argument(
    '--debug',
    action='store_true',
    help='print traceback and exit when an exception occurs')


def main():
    try:
        args = parser.parse_args()
        if not os.path.isdir(args.directory):
            print('{} is not a directory'.format(args.directory))
            return 2
        if args.delete or args.list_delete:
            cmd = delete_cmd
        else:
            cmd = verify_cmd
        all_ok = True
        for torrent_path in args.torrent:
            with open(torrent_path, 'rb') as f:
                torrent = bencode.bdecode(f.read())
                info = torrent['info']
                try:
                    ok = cmd(info, torrent_path, args)
                except Exception:
                    ok = False
                    print('{}: ERROR'.format(torrent_path))
                    if args.debug:
                        raise
                all_ok = all_ok and ok
        return 0 if all_ok else 1
    except KeyboardInterrupt:
        return 1


def delete_cmd(info, torrent_path, args):
    if 'files' not in info:
        return True
    base_path = os.path.join(args.directory, info['name'])
    paths = set(os.path.join(base_path, *f['path']) for f in info['files'])
    count = 0
    for dirpath, dirnames, filenames in os.walk(base_path):
        for filename in filenames:
            p = os.path.join(dirpath, filename)
            if p not in paths:
                count += 1
                if args.list_delete:
                    print('{}: {}'.format(torrent_path, p))
                if args.delete:
                    os.unlink(p)
    if count == 0:
        print('{}: OK'.format(torrent_path))
    else:
        verb = 'deleted' if args.delete else 'found'
        print('{}: {} extra file(s) {}'.format(torrent_path, count, verb))
    return True


def verify_cmd(info, torrent_path, args):
    ok = verify(info, args.directory)
    if ok:
        print('{}: OK'.format(torrent_path))
    else:
        print('{}: FAILED'.format(torrent_path))
    return ok


def verify(info, directory_path):
    """Return True if the checksum values in the torrent file match the
    computed checksum values of downloaded file(s) in the directory and if
    each file has the correct length as specified in the torrent file.
    """
    base_path = os.path.join(directory_path, info['name'])
    if 'length' in info:
        if os.stat(base_path).st_size != info['length']:
            return False
        getfile = lambda: open(base_path, 'rb')
    else:
        assert 'files' in info, 'invalid torrent file'
        for f in info['files']:
            p = os.path.join(base_path, *f['path'])
            if os.stat(p).st_size != f['length']:
                return False
        getfile = lambda: ConcatenatedFile(base_path, info['files'])
    with getfile() as f:
        return compare_checksum(info, f)


def compare_checksum(info, f):
    """Return True if the checksum values in the info dictionary match the
    computed checksum values of file content.
    """
    pieces = info['pieces']

    def getchunks(f, size):
        while True:
            chunk = f.read(size)
            if chunk == '':
                break
            yield hashlib.sha1(chunk).digest()

    calc = getchunks(f, info['piece length'])
    ref = (pieces[i:i + 20] for i in range(0, len(pieces), 20))
    for expected, actual in zip(calc, ref):
        if expected != actual:
            return False
    return ensure_empty(calc) and ensure_empty(ref)


def ensure_empty(gen):
    """Return True if the generator is empty.  If it is not empty, the first
    element is discarded.
    """
    try:
        next(gen)
        return False
    except StopIteration:
        return True


class ConcatenatedFile(object):
    """A file-like object that acts like a single file whose content is a
    concatenation of the specified files.  The returned object supports read(),
    __enter__() and __exit__().
    """

    def __init__(self, base, files):
        self._base = base
        self._files = files
        self._f = EmptyFile()
        self._i = -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._f.close()
        return False

    def read(self, size):
        if self._i == len(self._files):
            return ''
        buf = []
        count = 0
        while True:
            chunk = self._f.read(size - count)
            count += len(chunk)
            buf.append(chunk)
            if count < size:
                self._i += 1
                if self._i == len(self._files):
                    break
                p = os.path.join(self._base, *self._files[self._i]['path'])
                self._f.close()
                self._f = open(p, 'rb')
            else:
                break
        return ''.join(buf)


class EmptyFile(object):

    def read(self, size):
        return ''

    def close(self):
        return


if __name__ == '__main__':
    exit(main())
