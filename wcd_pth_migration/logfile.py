import sys


class UnrecognizedRippingLogException(Exception):
    pass


class InvalidRippingLogException(Exception):
    pass


class LogFile(object):
    def __init__(self, contents):
        self.contents = contents
        self.lines = contents.split('\n')
        if 'Exact Audio Copy' in self.contents:
            self._parse_eac_log()
        elif 'XLD extraction logfile' in self.contents:
            self._parse_xld_log()
        else:
            raise UnrecognizedRippingLogException()

    def _parse_xls_log(self):
        pass

    def _parse_eac_log(self):
        toc_entries = []
        state = 0
        for line in self.lines:
            if state == 0:
                if 'TOC of the extracted CD' in line:
                    state = 1
            elif state == 1:
                if line == '':
                    state = 2
                else:
                    raise InvalidRippingLogException()
            elif state == 2:
                if line == '     Track |   Start  |  Length  | Start sector | End sector':
                    state = 3
                else:
                    raise InvalidRippingLogException()
            elif state == 3:
                if line == '    ---------------------------------------------------------':
                    state = 4
                else:
                    raise InvalidRippingLogException()
            elif state == 4:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) == 5:
                    toc_entries.append({
                        'track': parts[0],
                        'start': parts[1],
                        'length': parts[2],
                        'start_sector': parts[3],
                        'end_sector': parts[4],
                    })
                else:
                    raise InvalidRippingLogException()


if __name__ == '__main__':
    log = sys.stdin.read()
    LogFile(log)
