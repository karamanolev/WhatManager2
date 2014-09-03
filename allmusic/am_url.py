# http://www.allmusic.com/album/complete-clapton-mw0000749969/credits
import re

url_re = re.compile('({0})?'.format(re.escape('http://www.allmusic.com')) + '''/
(?P<type> [/\w]+)/
(?P<name> [-\w]*)-
(?P<id>   \w+)
(
  $
  |
  /(?P<ext> .+)
)
''', re.VERBOSE)


def parse_url(url):
    r = url_re.search(url)
    r_dict = r.groupdict()
    return r_dict['type'], r_dict['id'], r_dict['ext'] or ''
