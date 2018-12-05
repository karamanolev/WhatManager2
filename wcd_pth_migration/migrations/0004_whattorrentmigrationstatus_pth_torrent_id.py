# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wcd_pth_migration', '0003_auto_20161206_1055'),
    ]

    operations = [
        migrations.AddField(
            model_name='whattorrentmigrationstatus',
            name='pth_torrent_id',
            field=models.BigIntegerField(null=True),
        ),
    ]
