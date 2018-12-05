# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wcd_pth_migration', '0004_whattorrentmigrationstatus_pth_torrent_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='TorrentGroupMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('what_group_id', models.BigIntegerField()),
                ('pth_group_id', models.BigIntegerField()),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='torrentgroupmapping',
            unique_together=set([('what_group_id', 'pth_group_id')]),
        ),
    ]
