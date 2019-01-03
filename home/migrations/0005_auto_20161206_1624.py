# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_auto_20161206_1038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downloadlocation',
            name='zone',
            field=models.CharField(max_length=32),
        ),
    ]
