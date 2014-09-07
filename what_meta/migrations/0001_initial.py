# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WhatArtist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('retrieved', models.DateTimeField()),
                ('name', models.CharField(max_length=200)),
                ('image', models.CharField(max_length=255, null=True)),
                ('wiki_body', models.TextField(null=True)),
                ('vanity_house', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WhatTorrentArtist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('importance', models.IntegerField()),
                ('artist', models.ForeignKey(to='what_meta.WhatArtist')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WhatTorrentGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('retrieved', models.DateTimeField()),
                ('wiki_body', models.TextField()),
                ('wiki_image', models.CharField(max_length=255)),
                ('joined_artists', models.TextField()),
                ('name', models.CharField(max_length=300)),
                ('year', models.IntegerField()),
                ('record_label', models.CharField(max_length=80)),
                ('catalogue_number', models.CharField(max_length=80)),
                ('release_type', models.IntegerField()),
                ('category_id', models.IntegerField()),
                ('category_name', models.CharField(max_length=32)),
                ('time', models.DateTimeField()),
                ('vanity_house', models.BooleanField(default=False)),
                ('torrents_json', models.TextField(null=True)),
                ('artists', models.ManyToManyField(to='what_meta.WhatArtist',
                                                   through='what_meta.WhatTorrentArtist')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='whattorrentartist',
            name='torrent_group',
            field=models.ForeignKey(to='what_meta.WhatTorrentGroup'),
            preserve_default=True,
        ),
    ]
