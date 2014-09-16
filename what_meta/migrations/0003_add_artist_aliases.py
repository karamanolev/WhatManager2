# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('what_meta', '0002_whatmetafulltext'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatArtistAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('artist', models.ForeignKey(to='what_meta.WhatArtist')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='whatmetafulltext',
            name='artist_alias',
            field=models.ForeignKey(null=True, to='what_meta.WhatArtistAlias', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='whattorrentartist',
            name='artist_alias',
            field=models.ForeignKey(to='what_meta.WhatArtistAlias', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='whatartist',
            name='name',
            field=models.CharField(max_length=200, db_index=True),
        ),
        migrations.AlterField(
            model_name='whatartist',
            name='retrieved',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.RunSQL(
            'ALTER TABLE `what_meta_whattorrentgroup` ADD INDEX `name_index` (`name` (200))',
            'ALTER TABLE `what_meta_whattorrentgroup` DROP INDEX `name_index`',
        ),
    ]
