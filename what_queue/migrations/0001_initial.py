# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='QueueItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('what_id', models.IntegerField()),
                ('priority', models.IntegerField()),
                ('artist', models.TextField()),
                ('title', models.TextField()),
                ('release_type', models.IntegerField()),
                ('format', models.TextField()),
                ('encoding', models.TextField()),
                ('torrent_size', models.BigIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
