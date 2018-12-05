# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wcd_pth_migration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatTorrentMigrationStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('what_torrent_id', models.BigIntegerField()),
                ('status', models.IntegerField()),
            ],
        ),
    ]
