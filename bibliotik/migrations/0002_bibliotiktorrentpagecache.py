# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bibliotik', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BibliotikTorrentPageCache',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('status_code', models.IntegerField()),
                ('headers', models.TextField()),
                ('body', models.TextField()),
            ],
        ),
    ]
