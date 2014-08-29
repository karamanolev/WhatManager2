import json
from django.shortcuts import render
from allmusic.am_parser import parse_artist, parse_artist_related, parse_search, parse_album
import am_download


def index(request):
    # d = am_download.download('http://www.allmusic.com/album/a-mw0002460486')
    # d = am_download.download('http://www.allmusic.com/song/winged-mt0046447536')
    # d = am_download.download('http://www.allmusic.com/song/django-mt0046447537')
    # d = am_download.download('http://www.allmusic.com/album/django-unchained-mw0002460486/releases')
    # d = am_download.download('http://www.allmusic.com/album/release/django-unchained-mr0003856413')
    # d = am_download.download('http://www.allmusic.com/mood/bombastic-xa0000000948')
    # d = am_download.download('http://www.allmusic.com/genre/pop-rock-ma0000002613')
    # d = am_download.download('http://www.allmusic.com/style/soundtracks-ma0000002867')
    # d = am_download.download('http://www.allmusic.com/artist/marillion-mn0000825924')
    # d = am_download.download('http://www.allmusic.com/artist/marillion-mn0000825924/related')
    # d = am_download.download('http://www.allmusic.com/album/release/fugazi-mr0001282654')
    # d = am_download.download('http://www.allmusic.com/album/fugazi-mw0000194759')
    d = am_download.download('http://www.allmusic.com/album/21-mw0002080092')

    # d = am_download.search('arcade fire the suburbs')
    parsed = parse_album(d)

    data = {
        'text': json.dumps(parsed, indent=2, sort_keys=True)
    }
    return render(request, 'allmusic/index.html', data)