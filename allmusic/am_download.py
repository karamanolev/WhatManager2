from django.utils.http import urlquote
import requests
from allmusic.am_url import parse_url
from allmusic.models import Download


def download(ref):
    if type(ref) is not tuple:
        ref = parse_url(ref)

    try:
        return Download.objects.get(
            type=ref[0],
            object_id=ref[1],
            extension=ref[2],
        )
    except Download.DoesNotExist:
        response = requests.get(
            'http://www.allmusic.com/{type}/a-{id}{ext}'.format(
                type=ref[0],
                id=ref[1],
                ext='/' + ref[2] if ref[2] else ''
            )
        )
        download = Download(
            type=ref[0],
            object_id=ref[1],
            extension=ref[2],
            html=response.text
        )
        download.save()
        return download


def search(query, type='albums'):
    response = requests.get(
        'http://www.allmusic.com/search/{type}/{query}'.format(
            type=type,
            query=urlquote(query)
        )
    )
    return response.text