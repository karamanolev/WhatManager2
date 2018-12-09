# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranscodeRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('requested_by_ip', models.TextField()),
                ('requested_by_what_user', models.TextField()),
                ('date_requested', models.DateTimeField(auto_now_add=True)),
                ('date_completed', models.DateTimeField(null=True)),
                ('celery_task_id', models.TextField(null=True)),
                ('what_torrent', models.ForeignKey(to='home.WhatTorrent', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
