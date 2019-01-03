# -*- coding: utf-8 -*-


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
            name='WhatFileMetadataCache',
            fields=[
                ('filename_sha256',
                 models.CharField(max_length=64, serialize=False, primary_key=True)),
                ('filename', models.CharField(max_length=500)),
                ('file_mtime', models.IntegerField()),
                ('metadata_pickle', models.BinaryField()),
                ('artists', models.CharField(max_length=200)),
                ('album', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200, db_index=True)),
                ('duration', models.FloatField()),
                ('what_torrent', models.ForeignKey(to='home.WhatTorrent', on_delete=models.CASCADE)),
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

        # Add indexes and fix fulltext
        migrations.RunSQL(
            'ALTER TABLE `home_whatfilemetadatacache` ENGINE = MYISAM',
            'ALTER TABLE `home_whatfilemetadatacache` ENGINE = INNODB',
            ),
        migrations.RunSQL(
            'ALTER TABLE `home_whatfilemetadatacache` ADD FULLTEXT `title_fts` (`title`)',
            'ALTER TABLE `home_whatfilemetadatacache` DROP INDEX `title_fts`',
            ),
        migrations.RunSQL(
            'ALTER TABLE `home_whatfilemetadatacache` ADD ' +
            'FULLTEXT `all_fts` (`artists`,`album`, `title`)',
            'ALTER TABLE `home_whatfilemetadatacache` DROP INDEX `all_fts`'
        ),
    ]
