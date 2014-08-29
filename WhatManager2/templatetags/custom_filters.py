import json

from django import template
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

from home.info_holder import get_release_type_name


register = template.Library()


@register.filter
def as_json(value):
    return mark_safe(json.dumps(value))


@register.filter(is_safe=True)
def filesizeformat(bytes):
    if bytes == 0:
        return '0 bytes'

    """
    Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 bytes, etc).
    """
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return '0 bytes'

    def filesize_number_format(value):
        if value < 10:
            return formats.number_format(round(value, 2), 2)
        elif value < 100:
            return formats.number_format(round(value, 2), 1)
        else:
            return formats.number_format(round(value, 1), 0)

    KB = 1 << 10
    MB = 1 << 20
    GB = 1 << 30
    TB = 1 << 40
    PB = 1 << 50

    sign = '-' if bytes < 0 else ''
    bytes = abs(bytes)

    if bytes == 0:
        return ugettext("0 bytes")
    if bytes < KB:
        if bytes != 1:
            return '{sign}{size:d} bytes'.format(sign=sign, size=int(bytes))
        else:
            return '1 byte'
    if bytes < MB:
        return ugettext("%s%s KB") % (sign, filesize_number_format(bytes / KB))
    if bytes < GB:
        return ugettext("%s%s MB") % (sign, filesize_number_format(bytes / MB))
    if bytes < TB:
        return ugettext("%s%s GB") % (sign, filesize_number_format(bytes / GB))
    if bytes < PB:
        return ugettext("%s%s TB") % (sign, filesize_number_format(bytes / TB))
    return ugettext("%s%s PB") % (sign, filesize_number_format(bytes / PB))


@register.filter
def tooltip_files_table(value):
    result = ['<table cellpadding="2">']
    for file in value:
        result.append('<tr><td>{0}</td><td style="text-align: right;">{1}</td></tr>'.format(
            file['name'],
            filesizeformat(file['size'])
        ))
    result.append('</table>')
    return ''.join(result)


@register.filter('release_type_name')
def filter_release_type_name(value):
    return get_release_type_name(value)


@register.filter
def what_cd_torrent_link(value):
    return u'https://what.cd/torrents.php?torrentid={0}'.format(value)


@register.filter
def timeformat(value):
    seconds = int(value % 60)
    value = int(value / 60)
    minutes = int(value % 60)
    value = int(value / 60)
    hours = int(value % 24)
    value = int(value / 24)
    days = int(value)
    return '{0:d}:{1:02d}:{2:02d}:{3:02d}'.format(days, hours, minutes, seconds)


@register.filter
def torrent_files(value):
    return ', '.join(f['name'] for f in value.info_files)
