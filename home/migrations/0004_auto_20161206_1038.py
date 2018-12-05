# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_file_metadata_cache_and_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='replicaset',
            name='zone',
            field=models.CharField(max_length=32),
        ),
    ]
