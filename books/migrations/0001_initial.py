# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('bibliotik', '0001_initial'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookUpload',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID',
                    serialize=False,
                    auto_created=True, primary_key=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('author', models.CharField(
                    max_length=1024,
                    null=True,
                    validators=[django.core.validators.MinLengthValidator(3)])),
                ('title', models.CharField(
                    max_length=512,
                    null=True,
                    validators=[django.core.validators.MinLengthValidator(3)])),
                ('isbn', models.CharField(
                    max_length=17,
                    null=True,
                    verbose_name=b'ISBN',
                    validators=[
                        django.core.validators.RegexValidator(b'^(97(8|9)-?)?\\d{9}(\\d|X)$')
                    ])),
                ('publisher', models.CharField(
                    max_length=256,
                    null=True,
                    validators=[django.core.validators.MinLengthValidator(3)])),
                ('pages', models.CharField(
                    max_length=6,
                    null=True,
                    blank=True)),
                ('year', models.IntegerField(
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(1000),
                        django.core.validators.MaxValueValidator(2015)
                    ])),
                ('format', models.CharField(
                    max_length=5,
                    null=True,
                    validators=[django.core.validators.MinLengthValidator(3)])),
                ('retail', models.BooleanField(default=False)),
                ('tags', models.CharField(
                    max_length=256,
                    null=True,
                    validators=[django.core.validators.MinLengthValidator(7)])),
                ('cover_url', models.CharField(
                    max_length=256,
                    null=True,
                    verbose_name=b'Cover URL',
                    blank=True)),
                ('description', models.TextField(
                    null=True,
                    validators=[django.core.validators.MinLengthValidator(100)])),
                ('target_filename', models.CharField(max_length=1024, null=True)),
                ('book_data', models.FileField(upload_to=b'book_data')),
                ('opf_data', models.TextField()),
                ('cover_data', models.BinaryField()),
                ('bibliotik_torrent_file', models.BinaryField(null=True)),
                ('what_torrent_file', models.BinaryField(null=True)),
                ('bibliotik_torrent', models.ForeignKey(
                    blank=True,
                    to='bibliotik.BibliotikTorrent',
                    null=True, 
                    on_delete=models.CASCADE)),
                ('what_torrent', models.ForeignKey(blank=True, to='home.WhatTorrent', 
                                                   null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
