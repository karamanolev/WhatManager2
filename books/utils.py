from subprocess import call


isbn_regex = '^(97(8|9)-?)?\d{9}(\d|X)$'


def fix_author(author):
    parts = author.split(', ')
    if len(parts) == 2:
        return parts[1] + ' ' + parts[0]
    return author


def call_mktorrent(target, torrent_filename, announce, torrent_name=None):
    args = [
        'mktorrent',
        '-a', announce,
        '-p',
        '-o', torrent_filename,
    ]
    if torrent_name:
        args.extend(('-n', torrent_name))
    args.append(target)
    if call(args) != 0:
        raise Exception('mktorrent returned non-zero')
