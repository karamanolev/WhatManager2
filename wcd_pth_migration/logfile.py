import json


class UnrecognizedRippingLogException(Exception):
    pass


class InvalidRippingLogException(Exception):
    pass


STATE_TOC = 0
STATE_TOC_HEADERS = 1
STATE_TOC_SEPARATOR = 2
STATE_TOC_ENTRY = 3
STATE_TRACK_HEADER = 4
STATE_PEAK_LEVEL = 5
STATE_END_OF_STATUS_REPORT = 6


class LogFile(object):
    def __init__(self, contents):
        if type(contents) is str:
            try:
                contents = contents.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    contents = contents.decode('utf-16')
                except UnicodeDecodeError:
                    contents = contents.decode('latin-1')
        self.contents = contents
        self.lines = contents.replace('\r', '').split('\n')
        if 'Exact Audio Copy' in self.contents or 'EAC extraction logfile' in self.contents:
            self._parse_eac_log()
        elif 'XLD extraction logfile' in self.contents:
            self._parse_xld_log()
        elif 'auCDtect' in self.contents:
            self._parse_non_log()
        else:
            raise UnrecognizedRippingLogException()

    def _parse_non_log(self):
        self.toc = []
        self.tracks = []

    def _parse_xld_log(self):
        track_entries = []
        toc_entries = []
        state = STATE_TOC
        for line in self.lines:
            if state == STATE_TOC:
                if 'TOC of the extracted CD' in line:
                    state = STATE_TOC_HEADERS
            elif state == STATE_TOC_HEADERS:
                if line == '':
                    pass
                elif line == '     Track |   Start  |  Length  | Start sector | End sector ':
                    state = STATE_TOC_SEPARATOR
                else:
                    raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
            elif state == STATE_TOC_SEPARATOR:
                if line.strip() == '---------------------------------------------------------':
                    state = STATE_TOC_ENTRY
                else:
                    raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
            elif state == STATE_TOC_ENTRY:
                if line == '':
                    state = STATE_TRACK_HEADER
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) == 5:
                    toc_entries.append({
                        'track': parts[0],
                        'start': parts[1],
                        'length': parts[2],
                        'start_sector': int(parts[3]),
                        'end_sector': int(parts[4]),
                    })
                else:
                    raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
            elif state == STATE_TRACK_HEADER:
                if line == '':
                    pass
                elif line == 'End of status report':
                    state = STATE_END_OF_STATUS_REPORT
                elif line.startswith('Track ') and not 'accurate' in line and 'confide' not in line:
                    current_track = int(line[len('Track '):])
                    track_entries.append({
                        'track': current_track,
                        'peak_level': None,
                    })
                    state = STATE_TRACK_HEADER
                elif line.strip().startswith('Peak'):
                    peak_level = line.strip()[len('Peak'):].strip(' \t\r\n:')
                    if len(track_entries):
                        track_entries[-1]['peak_level'] = peak_level
                    state = STATE_TRACK_HEADER
                else:
                    # Skip this for now
                    # raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
                    pass

        if state != STATE_END_OF_STATUS_REPORT:
            raise InvalidRippingLogException('Not in terminal state after end of log')
        self.toc = toc_entries
        self.tracks = track_entries

    def _parse_eac_log(self):
        track_entries = []
        toc_entries = []
        state = STATE_TOC
        for line in self.lines:
            if state == STATE_TOC:
                if 'TOC of the extracted CD' in line:
                    state = STATE_TOC_HEADERS
                elif line == 'End of status report':
                    state = STATE_END_OF_STATUS_REPORT
                elif line.startswith('Track ') and 'accurate' not in line and \
                                'databas' not in line and 'quality' not in line:
                    current_track = int(line[len('Track '):])
                    track_entries.append({
                        'track': current_track,
                    })
                    state = STATE_PEAK_LEVEL
            elif state == STATE_TOC_HEADERS:
                if line == '':
                    pass
                elif line == '     Track |   Start  |  Length  | Start sector | End sector ':
                    state = STATE_TOC_SEPARATOR
                else:
                    raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
            elif state == STATE_TOC_SEPARATOR:
                if line == '    ---------------------------------------------------------':
                    state = STATE_TOC_ENTRY
                else:
                    raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
            elif state == STATE_TOC_ENTRY:
                if line == '':
                    state = STATE_TOC  # TOC or track header
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) == 5:
                    toc_entries.append({
                        'track': parts[0],
                        'start': parts[1],
                        'length': parts[2],
                        'start_sector': int(parts[3]),
                        'end_sector': int(parts[4]),
                    })
                else:
                    raise InvalidRippingLogException('Got "{}" in state {}'.format(line, state))
            elif state == STATE_PEAK_LEVEL:
                if line.strip().startswith('Peak level'):
                    peak_level = line.strip()[len('Peak level'):].strip()
                    track_entries[-1]['peak_level'] = peak_level
                    state = STATE_TOC  # TOC or track header
            elif state == STATE_END_OF_STATUS_REPORT:
                pass
            else:
                raise Exception('Unknown state {}'.format(state))
        if state != STATE_END_OF_STATUS_REPORT:
            raise InvalidRippingLogException('Not in terminal state after end of log')
        self.toc = toc_entries
        self.tracks = track_entries

    def __eq__(self, other):
        if len(self.tracks) != len(other.tracks) or len(self.toc) != len(other.toc):
            return False
        if self.toc and other.toc:
            for track_a, track_b in zip(self.toc, other.toc):
                ta_len = track_a['end_sector'] - track_a['start_sector']
                tb_len = track_b['end_sector'] - track_a['start_sector']
                len_ratio = float(ta_len) / float(tb_len)
                if len_ratio < 0.99 or len_ratio > 1.01:
                    return False
        for track_a, track_b in zip(self.tracks, other.tracks):
            if track_a['peak_level'] != track_b['peak_level']:
                return False
        return True

    def __hash__(self):
        return hash(json.dumps([self.toc, self.tracks]))
