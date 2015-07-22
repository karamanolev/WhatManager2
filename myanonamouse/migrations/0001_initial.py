# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_file_metadata_cache_and_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='MAMLoginCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('cookies', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='MAMTorrent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('info_hash', models.CharField(max_length=40, db_index=True)),
                ('title', models.CharField(max_length=256)),
                ('retrieved', models.DateTimeField()),
                ('category', models.CharField(max_length=32)),
                ('subcategory', models.CharField(max_length=64)),
                ('language', models.CharField(max_length=32)),
                ('isbn', models.CharField(max_length=16)),
                ('cover_url', models.TextField(null=True)),
                ('small_description', models.TextField()),
                ('description', models.TextField()),
                ('html_page', models.TextField()),
                ('torrent_url', models.TextField(null=True)),
                ('torrent_filename', models.TextField(null=True)),
                ('torrent_file', models.BinaryField(null=True)),
                ('torrent_size', models.BigIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MAMTransTorrent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('info_hash', models.CharField(max_length=40)),
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
                ('mam_torrent', models.ForeignKey(to='myanonamouse.MAMTorrent')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
