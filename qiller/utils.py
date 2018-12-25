
import logging
import os.path
import re
from subprocess import call
import time

logger = logging.getLogger(__name__)


def strip_path_chars(path):
    return ''.join(c for c in path if c not in '\/:*?"<>|')


def time_text(seconds):
    assert type(seconds) == int
    return '{0}:{1:02}'.format(seconds // 60, seconds % 60)


def ensure_file_dir_exists(file_path):
    dir_name = os.path.dirname(file_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


class FLACTester(object):
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def test(self, track):
        file_path = os.path.join(self.temp_dir, track.temp_filename)
        logger.debug('Testing FLAC integrity for {0}'.format(file_path))
        args = ['flac', '-t', '--totally-silent', file_path]
        if call([a for a in args]) != 0:
            raise Exception('flac -t returned non-zero. Corrupt file?')
        logger.debug('FLAC integrity test complete'.format(file_path))


def download_test_spectral(downloader, flac_tester, spectrals, track):
    downloader.download_track(track)
    flac_tester.test(track)
    spectrals.generate_spectral(track)


def retry_action(action):
    i = 0
    while True:
        try:
            return action()
        except Exception as ex:
            raise
            i += 1
            if i == 3:
                raise
            print('Failed with {0}, retrying...'.format(ex))
            time.sleep(3)


records_words = ['records', 'recordings', 'production', 'productions', 'distribution', 'music']
strip_fixes = ['(c)', ' c', ' c', '\u00A9', 'inc.', 'ltd', 'ltd.', 'limited']


def extract_label(copyright):
    if '/' in copyright:
        parts = copyright.split('/', 1)
        label = parts[-1].lower().strip()
        if label == 'ada us':
            label = parts[0].lower().strip()
    else:
        label = copyright.lower().strip()
    for word in records_words:
        if word in copyright.lower() and word not in label:
            label += ' ' + word
    for fix in strip_fixes:
        if label.startswith(fix):
            label = label[len(fix):].strip()
        if label.endswith(fix):
            label = label[:-len(fix)].strip()
    label = re.sub('[0-9]{4}', '', label).strip()
    label = label.strip().title()
    if 'Ada ' in label:
        label = label.replace('Ada', 'ADA')
    return label
