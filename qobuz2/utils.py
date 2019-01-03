import os.path
import re

from WhatManager2.settings import MEDIA_ROOT


def get_temp_dir(qobuz_id):
    return os.path.join(MEDIA_ROOT, 'qobuz_uploads', str(qobuz_id))


def title(value):
    """Converts a string into titlecase."""
    t = re.sub("([a-z])'([A-Z])", lambda m: m.group(0).lower(), value.title())
    t = re.sub("\d([A-Z])", lambda m: m.group(0).lower(), t)
    t = t.replace("I'M", "I'm")
    return t
