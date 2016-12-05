from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, render


# Create your views here.
from bibliotik.utils import upload_book_to_bibliotik, BibliotikClient
from books.models import BookUpload


@login_required
def upload_book(request, book_upload_id):
    bibliotik_id = request.GET['bibliotik_id']
    book_upload = BookUpload.objects.get(id=book_upload_id)
    bibliotik_client = BibliotikClient(bibliotik_id)
    upload_book_to_bibliotik(bibliotik_client, book_upload)
    return redirect(request.GET['return'])


@login_required
def refresh_ui(request):
    return render(request, 'bibliotik/refresh_ui.html')


@login_required
def cache_worker(request):
    return render(request, 'bibliotik/cache_worker.html')
