# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WhatUserSnapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('user_id', models.IntegerField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('uploaded', models.BigIntegerField()),
                ('downloaded', models.BigIntegerField()),
                ('info', models.TextField()),
            ],
            options={
                'permissions': (('view_whatusersnapshot', 'Can view the user profile.'),),
            },
            bases=(models.Model,),
        ),
    ]
