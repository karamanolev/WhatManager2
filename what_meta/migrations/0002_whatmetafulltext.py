# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('what_meta', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatMetaFulltext',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('info', models.TextField()),
                ('more_info', models.TextField()),
                ('artist', models.ForeignKey(null=True, to='what_meta.WhatArtist', 
                                             unique=True, on_delete=models.CASCADE)),
                ('torrent_group', models.ForeignKey(null=True, to='what_meta.WhatTorrentGroup', 
                                                    unique=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),

        # Add indexes and fix fulltext
        migrations.RunSQL(
            'ALTER TABLE `what_meta_whatmetafulltext` ENGINE = MYISAM',
            'ALTER TABLE `what_meta_whatmetafulltext` ENGINE = INNODB',
            ),
        migrations.RunSQL(
            'ALTER TABLE `what_meta_whatmetafulltext` ADD FULLTEXT `info_fts` (`info`)',
            'ALTER TABLE `what_meta_whatmetafulltext` DROP INDEX `info_fts`',
            ),
        migrations.RunSQL(
            'ALTER TABLE `what_meta_whatmetafulltext` ADD ' +
            'FULLTEXT `info_more_info_fts` (`info`,`more_info`)',
            'ALTER TABLE `what_meta_whatmetafulltext` DROP INDEX `info_more_info_fts`'
        ),
    ]
