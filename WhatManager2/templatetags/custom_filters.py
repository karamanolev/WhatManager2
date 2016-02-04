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
def filesizeformat(value):
    if value == 0:
        return '0 bytes'

    """
    Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 bytes, etc).
    """
    try:
        value = float(value)
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

    sign = '-' if value < 0 else ''
    value = abs(value)

    if value == 0:
        return ugettext("0 bytes")
    if value < KB:
        if value != 1:
            return '{sign}{size:d} bytes'.format(sign=sign, size=int(value))
        else:
            return '1 byte'
    if value < MB:
        return ugettext("%s%s KB") % (sign, filesize_number_format(value / KB))
    if value < GB:
        return ugettext("%s%s MB") % (sign, filesize_number_format(value / MB))
    if value < TB:
        return ugettext("%s%s GB") % (sign, filesize_number_format(value / GB))
    if value < PB:
        return ugettext("%s%s TB") % (sign, filesize_number_format(value / TB))
    return ugettext("%s%s PB") % (sign, filesize_number_format(value / PB))


@register.filter
def tooltip_files_table(value):
    result = [u'<table cellpadding="2">']
    for filename in value:
        result.append(u'<tr><td>{0}</td><td style="text-align: right;">{1}</td></tr>'.format(
            filename['name'], filesizeformat(filename['size'])
        ))
    result.append(u'</table>')
    return u''.join(result)


@register.filter('release_type_name')
def filter_release_type_name(value):
    return get_release_type_name(value)


@register.filter
def what_cd_torrent_link(value):
    return u'https://what.cd/torrents.php?torrentid={0}'.format(value)


@register.filter
def bibliotik_torrent_link(value):
    return u'https://bibliotik.me/torrents/{0}'.format(value)


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


@register.filter
def type_name(value):
    return type(value).__name__
