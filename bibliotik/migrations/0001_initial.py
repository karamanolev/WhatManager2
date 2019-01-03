# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BibliotikFulltext',
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
            name='BibliotikTorrent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('info_hash', models.CharField(max_length=40, db_index=True)),
                ('retrieved', models.DateTimeField()),
                ('category', models.CharField(max_length=32)),
                ('format', models.CharField(max_length=16)),
                ('retail', models.BooleanField(default=False)),
                ('pages', models.IntegerField()),
                ('language', models.CharField(max_length=32)),
                ('isbn', models.CharField(max_length=16)),
                ('cover_url', models.TextField()),
                ('tags', models.TextField()),
                ('publisher', models.TextField()),
                ('year', models.IntegerField(null=True)),
                ('author', models.TextField()),
                ('title', models.TextField()),
                ('html_page', models.TextField()),
                ('torrent_filename', models.TextField(null=True)),
                ('torrent_file', models.BinaryField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BibliotikTransTorrent',
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
                ('bibliotik_torrent', models.ForeignKey(to='bibliotik.BibliotikTorrent', 
                                                        on_delete=models.CASCADE)),
                ('instance', models.ForeignKey(to='home.TransInstance', on_delete=models.CASCADE)),
                ('location', models.ForeignKey(to='home.DownloadLocation', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),

        # Add indexes and fix fulltext
        migrations.RunSQL(
            'ALTER TABLE `bibliotik_bibliotikfulltext` ENGINE = MYISAM',
            'ALTER TABLE `bibliotik_bibliotikfulltext` ENGINE = INNODB',
        ),
        migrations.RunSQL(
            'ALTER TABLE `bibliotik_bibliotikfulltext` ADD FULLTEXT `info_fts` (`info`)',
            'ALTER TABLE `bibliotik_bibliotikfulltext` DROP INDEX `info_fts`',
        ),
        migrations.RunSQL(
            'ALTER TABLE `bibliotik_bibliotikfulltext` ADD ' +
            'FULLTEXT `info_more_info_fts` (`info`,`more_info`)',
            'ALTER TABLE `bibliotik_bibliotikfulltext` DROP INDEX `info_more_info_fts`'
        ),
    ]
