# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def drop_datetime_index(apps, schema_editor):
    try:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('ALTER TABLE `home_logentry` DROP INDEX `datetime_index`')
    except Exception:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0002_add_torrent_group_fk'),
    ]

    operations = [
        migrations.RunPython(drop_datetime_index),
        migrations.CreateModel(
            name='FileMetadataCache',
            fields=[
                ('filename_sha256', models.CharField(max_length=64, serialize=False,
                                                     primary_key=True)),
                ('filename', models.TextField()),
                ('file_mtime', models.IntegerField()),
                ('metadata_pickle', models.BinaryField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='logentry',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='whattorrent',
            name='retrieved',
            field=models.DateTimeField(db_index=True),
        ),
    ]
