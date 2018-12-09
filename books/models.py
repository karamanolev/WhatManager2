from django import forms
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator, \
    RegexValidator
from django.db import models
from django.forms.models import ModelForm
import pyquery

from books.utils import isbn_regex
import what_transcode.utils
from books import utils


class BookUpload(models.Model):
    binary_fields = ['opf_data', 'cover_data', 'bibliotik_torrent_file', 'what_torrent_file']

    added = models.DateTimeField(auto_now_add=True)
    author = models.CharField(null=True, max_length=1024, validators=[MinLengthValidator(3)])
    title = models.CharField(null=True, max_length=512, validators=[MinLengthValidator(3)])
    isbn = models.CharField("ISBN", null=True, max_length=17,
                            validators=[RegexValidator(isbn_regex)])
    publisher = models.CharField(null=True, max_length=256, validators=[MinLengthValidator(3)])
    pages = models.CharField(null=True, max_length=6, blank=True)
    year = models.IntegerField(null=True, validators=[MinValueValidator(1000),
                                                      MaxValueValidator(2015)])
    format = models.CharField(null=True, max_length=5, validators=[MinLengthValidator(3)])
    retail = models.BooleanField(default=False)
    tags = models.CharField(null=True, max_length=256, validators=[MinLengthValidator(7)])
    cover_url = models.CharField('Cover URL', null=True, blank=True, max_length=256)
    description = models.TextField(null=True, validators=[MinLengthValidator(100)])
    target_filename = models.CharField(null=True, max_length=1024)

    book_data = models.FileField(upload_to='book_data')
    opf_data = models.TextField()
    cover_data = models.BinaryField()
    bibliotik_torrent_file = models.BinaryField(null=True)
    what_torrent_file = models.BinaryField(null=True)

    bibliotik_torrent = models.ForeignKey('bibliotik.BibliotikTorrent', null=True, blank=True, on_delete=models.CASCADE)
    what_torrent = models.ForeignKey('home.WhatTorrent', null=True, blank=True, on_delete=models.CASCADE)

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(';')]

    @tag_list.setter
    def tag_list(self, value):
        self.tags = ';'.join(value)

    def populate_from_opf(self):
        pq = pyquery.PyQuery(self.opf_data.encode('utf-8'))
        nss = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf',
        }
        self.author = ', '.join(utils.fix_author(creator.text()) for creator in
                                list(pq('dc|creator', namespaces=nss).items()))
        self.title = pq('dc|title', namespaces=nss).text()
        isbns = pq('dc|identifier[opf|scheme="ISBN"]:first', namespaces=nss)
        if len(isbns) > 0:
            self.isbn = isbns.text()
        self.publisher = pq('dc|publisher', namespaces=nss).text()
        self.year = pq('dc|date', namespaces=nss).text()[:4]
        self.description = pq('dc|description', namespaces=nss).text()
        self.target_filename = what_transcode.utils.fix_pathname(
            self.title + ' - ' + self.author + '.' + self.format.lower())


class BookUploadForm(ModelForm):
    class Meta:
        model = BookUpload
        fields = ['author', 'title', 'isbn', 'publisher', 'cover_url', 'pages', 'year', 'format',
                  'retail', 'tags', 'target_filename', 'description']

    def __init__(self, *args, **kwargs):
        super(BookUploadForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields.get(field_name)
            if type(field) not in [forms.BooleanField]:
                pass  # field.widget.attrs['style'] = 'width: 400px;'
