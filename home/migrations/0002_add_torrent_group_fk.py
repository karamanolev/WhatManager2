# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from WhatManager2.management.commands import what_meta_fixer


def run_meta_fixer(apps, schema_editor):
    WhatTorrent = apps.get_model('home', 'WhatTorrent')
    meta_fixer = what_meta_fixer.Command(WhatTorrent)
    meta_fixer.handle()


class Migration(migrations.Migration):
    dependencies = [
        ('what_meta', '0001_initial'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='whattorrent',
            name='what_group_id',
        ),
        migrations.AddField(
            model_name='whattorrent',
            name='torrent_group',
            field=models.ForeignKey(to='what_meta.WhatTorrentGroup', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(run_meta_fixer, reverse_code=lambda apps, schema_editor: None)
    ]
