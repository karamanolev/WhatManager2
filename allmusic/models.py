from django.db import models
from django.utils.functional import cached_property
from pyquery.pyquery import PyQuery


class Download(models.Model):
    datetime_retrieved = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=128)
    object_id = models.CharField(max_length=128)
    extension = models.CharField(max_length=128)
    html = models.TextField()

    @cached_property
    def pq(self):
        return PyQuery(self.html)
