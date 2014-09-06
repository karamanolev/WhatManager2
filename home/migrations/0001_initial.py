# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

import home.info_holder


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('zone', models.CharField(max_length=16)),
                ('path', models.TextField()),
                ('preferred', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('type', models.TextField()),
                ('message', models.TextField()),
                ('traceback', models.TextField(null=True)),
                ('user', models.ForeignKey(related_name=b'wm_logentry',
                                           to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'permissions': (('view_logentry', 'Can view the logs.'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReplicaSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('zone', models.CharField(max_length=16)),
                ('name', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TransInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('name', models.TextField()),
                ('host', models.TextField()),
                ('port', models.IntegerField()),
                ('peer_port', models.IntegerField()),
                ('username', models.TextField()),
                ('password', models.TextField()),
                ('replica_set', models.ForeignKey(to='home.ReplicaSet')),
            ],
            options={
                'permissions': (
                    ('view_transinstance_stats', 'Can view current Transmission stats.'),
                    ('run_checks', 'Can run the validity checks.')
                ),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WhatFulltext',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('info', models.TextField()),
                ('more_info', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WhatLoginCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('cookies', models.TextField()),
                ('authkey', models.TextField()),
                ('passkey', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WhatTorrent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('info_hash', models.TextField()),
                ('torrent_file', models.TextField()),
                ('torrent_file_name', models.TextField()),
                ('retrieved', models.DateTimeField()),
                ('info', models.TextField()),
                ('tags', models.TextField()),
                ('what_group_id', models.IntegerField()),
                ('added_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'permissions': (
                    ('view_whattorrent', 'Can view torrents.'),
                    ('download_whattorrent', 'Can download and play torrents.')
                ),
            },
            bases=(models.Model, home.info_holder.InfoHolder),
        ),
        migrations.CreateModel(
            name='TransTorrent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('info_hash', models.TextField()),
                ('torrent_id', models.IntegerField(null=True)),
                ('torrent_name', models.TextField(null=True)),
                ('torrent_size', models.BigIntegerField(null=True)),
                ('torrent_uploaded', models.BigIntegerField(null=True)),
                ('torrent_done', models.FloatField(null=True)),
                ('torrent_date_added', models.DateTimeField(null=True)),
                ('torrent_error', models.IntegerField(null=True)),
                ('torrent_error_string', models.TextField(null=True)),
                ('instance', models.ForeignKey(to='home.TransInstance')),
                ('location', models.ForeignKey(to='home.DownloadLocation')),
                ('what_torrent', models.ForeignKey(to='home.WhatTorrent')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),

        # Add indexes and fix fulltext
        migrations.RunSQL(
            'ALTER TABLE `home_logentry` ADD INDEX `datetime_index` (`datetime`)',
            'ALTER TABLE `home_logentry` DROP INDEX `datetime_index`',
        ),
        migrations.RunSQL(
            'ALTER TABLE `home_whatfulltext` ENGINE = MYISAM',
            'ALTER TABLE `home_whatfulltext` ENGINE = INNODB',
        ),
        migrations.RunSQL(
            'ALTER TABLE `home_whatfulltext` ADD FULLTEXT `info_fts` (`info`)',
            'ALTER TABLE `home_whatfulltext` DROP INDEX `info_fts`',
        ),
        migrations.RunSQL(
            'ALTER TABLE `home_whattorrent` ADD INDEX `info_hash_index` (`info_hash` (40))',
            'ALTER TABLE `home_whattorrent` DROP INDEX `info_hash_index`',
        ),
    ]
