import pickle

from django import forms
from django.core.validators import RegexValidator
from django.db import models



# Create your models here.
from django.forms.formsets import BaseFormSet
from django.utils.functional import cached_property
from qiller.metadata import WHAT_ARTIST_TYPES
from qiller.qobuz_api import QobuzAPI
from qiller.tidal_api import TidalAPI
from qobuz2 import settings
from qobuz2.settings import TIDAL_SESSION_ID


class QobuzUpload(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    qobuz_album_id = models.CharField(max_length=64)
    state = models.IntegerField()
    upload_pickle = models.BinaryField()
    download_task_id = models.CharField(max_length=64, null=True)

    def save(self, *args, **kwargs):
        upload = pickle.loads(self.upload_pickle)
        self.qobuz_album_id = upload.metadata.id
        self.state = upload.state
        super(QobuzUpload, self).save(*args, **kwargs)

    @cached_property
    def upload(self):
        return pickle.loads(self.upload_pickle)

    def set_upload(self, upload):
        self.qobuz_album_id = upload.metadata.id
        self.state = upload.state
        self.upload_pickle = pickle.dumps(upload)


class LoginDataCache(models.Model):
    data = models.TextField()

    @classmethod
    def get_state(cls):
        try:
            cache = LoginDataCache.objects.get()
            return cache.data
        except LoginDataCache.DoesNotExist:
            return None

    @classmethod
    def set_state(cls, data):
        cache = LoginDataCache(data=data)
        cache.save()


def get_qobuz_client(request):
    if not hasattr(request, 'qobuz_client'):
        request.qobuz_client = QobuzAPI(settings.QOBUZ_USERNAME, settings.QOBUZ_PASSWORD,
                                        LoginDataCache.get_state, LoginDataCache.set_state)
    return request.qobuz_client


def get_tidal_client(request):
    if not hasattr(request, 'tidal_client'):
        request.tidal_client = TidalAPI(TIDAL_SESSION_ID)
    return request.tidal_client


class NewUploadForm(forms.Form):
    album_id = forms.CharField(max_length=32, validators=[RegexValidator('^[0-9]+$')])


class EditUploadForm(forms.Form):
    joined_artists = forms.CharField()
    title = forms.CharField()
    label = forms.CharField(required=False)
    year = forms.CharField(required=False, max_length=7)
    genre = forms.CharField()

    def __init__(self, *args, **kwargs):
        metadata = kwargs.pop('metadata')
        kwargs['initial'] = metadata.__dict__
        super(EditUploadForm, self).__init__(*args, **kwargs)


class EditTrackForm(forms.Form):
    joined_artists = forms.CharField()
    title = forms.CharField()
    track_number = forms.IntegerField()
    media_number = forms.IntegerField()


class EditTracksFormSet(BaseFormSet):
    form = EditTrackForm
    min_num = 0
    max_num = 10000
    extra = 0
    can_order = False
    can_delete = False
    absolute_max = 10000
    validate_max = False
    validate_min = False

    def __init__(self, *args, **kwargs):
        metadata = kwargs.pop('metadata')
        kwargs['initial'] = [t.__dict__ for t in metadata.tracks]
        super(EditTracksFormSet, self).__init__(*args, **kwargs)


class EditArtistForm(forms.Form):
    name = forms.CharField()
    artist_type = forms.ChoiceField(choices=list(WHAT_ARTIST_TYPES.items()))


class EditArtistsFormSet(BaseFormSet):
    form = EditArtistForm
    min_num = 0
    max_num = 10000
    extra = 0
    can_order = False
    can_delete = False
    absolute_max = 10000
    validate_max = False
    validate_min = False

    def __init__(self, *args, **kwargs):
        metadata = kwargs.pop('metadata')
        kwargs['initial'] = [t.__dict__ for t in metadata.artists]
        super(EditArtistsFormSet, self).__init__(*args, **kwargs)
