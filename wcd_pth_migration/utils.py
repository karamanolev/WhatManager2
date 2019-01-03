import os
import shutil
from subprocess import Popen

from django.conf import settings


def generate_spectrals_for_dir(dir_path):
    try:
        shutil.rmtree(settings.WCD_PTH_SPECTRALS_HTML_PATH)
    except OSError:
        pass
    os.makedirs(settings.WCD_PTH_SPECTRALS_HTML_PATH)
    html_file = open(os.path.join(settings.WCD_PTH_SPECTRALS_HTML_PATH, 'index.html'), 'w')
    html_file.write('<html><body><table border="0">')
    spectral_num = 1
    subprocess_calls = []
    for dirpath, dirnames, filenames in os.walk(dir_path):
        for filename in filenames:
            if not filename.lower().endswith('flac'):
                continue
            filepath = os.path.join(dirpath, filename)
            full_dest_path = os.path.join(settings.WCD_PTH_SPECTRALS_HTML_PATH,
                                          '{0:02}.full.png'.format(spectral_num))
            zoom_dest_path = os.path.join(settings.WCD_PTH_SPECTRALS_HTML_PATH,
                                          '{0:02}.zoom.png'.format(spectral_num))
            args = [
                'sox', filepath, '-n', 'remix', '1', 'spectrogram', '-x', '3000', '-y', '513',
                '-w',
                'Kaiser', '-S', '0:40', '-d', '0:04', '-h', '-t',
                '{0} Zoom'.format(filename.decode('utf-8')),
                '-o', zoom_dest_path
            ]
            subprocess_calls.append(args)
            args = [
                'sox', filepath, '-n', 'remix', '1', 'spectrogram', '-x', '3000', '-y', '513',
                '-w',
                'Kaiser', '-h', '-t', '{0} Full'.format(
                    filename.decode('utf-8')), '-o', full_dest_path
            ]
            subprocess_calls.append(args)
            html_file.write('<tr><td><img src="{}"></td><td><img src="{}"></td></tr>'.format(
                os.path.basename(full_dest_path), os.path.basename(zoom_dest_path)))
            spectral_num += 1
    html_file.write('</table></body></html>')
    html_file.close()
    subprocesses = [Popen(call) for call in subprocess_calls]
    for process in subprocesses:
        process.wait()
        if process.returncode != 0:
            raise Exception('sox returned non-zero')
    return spectral_num - 1


def normalize_for_matching(s):
    return s.lower().replace(' ', '').replace('-', '').replace('/', '')
