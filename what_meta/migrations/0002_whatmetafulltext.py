# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('what_meta', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatMetaFulltext',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('info', models.TextField()),
                ('more_info', models.TextField()),
                ('artist', models.ForeignKey(null=True, to='what_meta.WhatArtist', unique=True)),
                ('torrent_group', models.ForeignKey(null=True, to='what_meta.WhatTorrentGroup', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
