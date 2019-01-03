# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('what_meta', '0003_add_artist_aliases'),
    ]

    operations = [
        migrations.AlterField(
            model_name='whatmetafulltext',
            name='artist',
            field=models.OneToOneField(null=True, 
                                       to='what_meta.WhatArtist', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='whatmetafulltext',
            name='artist_alias',
            field=models.OneToOneField(null=True, 
                                       to='what_meta.WhatArtistAlias', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='whatmetafulltext',
            name='torrent_group',
            field=models.OneToOneField(null=True, 
                                       to='what_meta.WhatTorrentGroup', on_delete=models.CASCADE),
        ),
    ]