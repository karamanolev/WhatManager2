# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wcd_pth_migration', '0002_whattorrentmigrationstatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='whattorrentmigrationstatus',
            name='what_torrent_id',
            field=models.BigIntegerField(unique=True),
        ),
    ]
