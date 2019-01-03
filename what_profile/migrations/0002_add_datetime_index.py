# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('what_profile', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='whatusersnapshot',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
