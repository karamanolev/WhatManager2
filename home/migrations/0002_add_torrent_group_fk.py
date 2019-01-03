# -*- coding: utf-8 -*-


from django.db import models, migrations


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
            field=models.ForeignKey(to='what_meta.WhatTorrentGroup', 
                                    null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
