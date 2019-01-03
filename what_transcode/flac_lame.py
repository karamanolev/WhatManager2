import os
from subprocess import PIPE, Popen

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

from what_transcode.utils import get_sample_rate, get_bit_depth


def execute_chain(chain_options):
    processes = []
    for options in chain_options:
        if processes:
            p_stdin = processes[-1].stdout
        else:
            p_stdin = None
        if options == chain_options[-1]:
            p_stdout = None
        else:
            p_stdout = PIPE

        p = Popen(options, stdin=p_stdin, stdout=p_stdout)
        processes.append(p)

    for p in reversed(processes):
        p.communicate()

    for p in processes:
        if p.returncode != 0:
            print(p.returncode)
            raise Exception('Subprocess returned non-zero')


def transcode_file(source_file, dest_file, source_media, bitrate):
    source_samplerate = get_sample_rate(source_file)
    source_bit_depth = get_bit_depth(source_file)
    if source_media == 'SACD':
        assert source_samplerate >= 88200
        target_samplerate = 44100
        print('Source is SACD, will resample to {0}'.format(target_samplerate))
    else:
        target_samplerate = {
            44100: None,
            48000: None,
            88200: 44100,
            96000: 48000,
            176400: 44100,
            192000: 48000,
        }[source_samplerate]
        print('Source is NOT SACD, will resample to {0}'.format(target_samplerate))

    try:
        os.makedirs(os.path.dirname(dest_file))
    except OSError:
        pass

    flac_options = ['flac', '-d', '-c', source_file]
    lame_options = ['lame', '-h']
    if bitrate == '320':
        lame_options += ['--cbr', '-b', '320']
    elif bitrate == 'V0':
        lame_options += ['-V', '0']
    elif bitrate == 'V2':
        lame_options += ['-V', '2']
    else:
        raise Exception('Unknown bitrate')
    lame_options += ['-', dest_file]

    if target_samplerate is None and source_bit_depth == 16:
        chain_options = [flac_options, lame_options]
    else:
        target_samplerate = target_samplerate or source_samplerate
        sox_options = ['sox', '-t', 'wav', '-', '-b', '16', '-t', 'wav', '-', 'rate', '-v', '-L',
                       str(target_samplerate), 'dither']
        chain_options = [flac_options, sox_options, lame_options]

    print('Chain is', chain_options)
    execute_chain(chain_options)

    if not os.path.isfile(dest_file) or os.path.getsize(dest_file) < 1024:
        raise Exception('Missing output file or is less than 1K')

    flacfile = FLAC(source_file)
    try:
        mp3file = EasyID3(dest_file)
    except mutagen.id3.ID3NoHeaderError:
        mp3file = mutagen.File(dest_file, easy=True)
        mp3file.add_tags()
    for tag in flacfile:
        if tag in list(EasyID3.valid_keys.keys()):
            mp3file[tag] = flacfile[tag]
    mp3file.save()
