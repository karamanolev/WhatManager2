import os

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect

from WhatManager2 import whatimg
import bibliotik.settings
import WhatManager2.settings
from books import settings, utils, what_upload
from books.models import BookUploadForm, BookUpload


@login_required
def uploads(request):
    books = BookUpload.objects.defer(*BookUpload.binary_fields).order_by('-added').all()
    data = {
        'books': books
    }
    return render(request, 'books/uploads.html', data)


@login_required
def new_upload(request):
    errors = []
    if request.method == 'POST':
        if 'ebook' in request.FILES and 'opf' in request.FILES and 'cover' in request.FILES:
            if os.path.splitext(request.FILES['ebook'].name)[1] not in ['.azw3', '.epub', '.pdf']:
                errors.append('What is this ebook extension?')
            elif os.path.splitext(request.FILES['opf'].name)[1] != '.opf':
                errors.append('What is this OPF?')
            elif os.path.splitext(request.FILES['cover'].name)[1] not in ['.jpg', '.jpeg']:
                errors.append('What is this cover?')
            else:
                book_upload = BookUpload()
                book_upload.book_data = request.FILES['ebook']
                book_upload.opf_data = request.FILES['opf'].read().decode('utf-8')
                book_upload.cover_data = request.FILES['cover'].read()
                book_upload.format = os.path.splitext(request.FILES['ebook'].name)[1][1:].upper()
                book_upload.save()
                return redirect('books-edit_upload', book_upload.id)
        else:
            errors.append('Please upload the ebook, the OPF and the cover')
    data = {
        'errors': errors
    }
    return render(request, 'books/new_upload.html', data)


@login_required
def edit_upload(request, upload_id):
    book_upload = BookUpload.objects.defer(*BookUpload.binary_fields).extra(
        select={
            'has_bibliotik_torrent': '`bibliotik_torrent_file` IS NOT NULL '
                                     'AND OCTET_LENGTH(`bibliotik_torrent_file`) != 0',
            'has_what_torrent': '`what_torrent_file` IS NOT NULL '
                                'AND OCTET_LENGTH(`what_torrent_file`) != 0',
        }).get(id=upload_id)

    if book_upload.title is None:
        book_upload.populate_from_opf()
        book_upload.save()

    if request.method == 'POST':
        form = BookUploadForm(request.POST, instance=book_upload)
        if form.is_valid():
            form.save()
    else:
        form = BookUploadForm(instance=book_upload)

    try:
        book_upload.full_clean()
        book_upload.is_valid = True
    except ValidationError:
        book_upload.is_valid = False

    data = {
        'book': book_upload,
        'form': form
    }
    return render(request, 'books/edit_upload.html', data)


@login_required
def upload_cover(request, upload_id):
    book_upload = BookUpload.objects.only('cover_data').get(id=upload_id)
    return HttpResponse(book_upload.cover_data, content_type='image/jpeg')


@login_required
def upload_cover_upload(request, upload_id):
    book_upload = BookUpload.objects.only('cover_url', 'cover_data').get(id=upload_id)
    if not book_upload.cover_url:
        whatimg_url = whatimg.upload_image_from_memory(book_upload.cover_data)
        book_upload.cover_url = whatimg_url
        book_upload.save()
    return redirect('books-edit_upload', upload_id)


@login_required
def upload_generate_torrents(request, upload_id):
    book_upload = BookUpload.objects.get(id=upload_id)
    target_temp_filename = book_upload.book_data.storage.path(book_upload.book_data)
    torrent_temp_filename = os.path.join(settings.UPLOAD_TEMP_DIR,
                                         os.path.splitext(book_upload.target_filename)[
                                             0] + '.torrent')

    if book_upload.bibliotik_torrent_file is None:
        utils.call_mktorrent(target_temp_filename,
                             torrent_temp_filename,
                             bibliotik.settings.BIBLIOTIK_ANNOUNCE,
                             book_upload.target_filename)
        with open(torrent_temp_filename, 'rb') as file:
            book_upload.bibliotik_torrent_file = file.read()
        book_upload.save()
        os.remove(torrent_temp_filename)

    if book_upload.what_torrent_file is None:
        utils.call_mktorrent(target_temp_filename,
                             torrent_temp_filename,
                             WhatManager2.settings.WHAT_ANNOUNCE,
                             book_upload.target_filename)
        with open(torrent_temp_filename, 'rb') as file:
            book_upload.what_torrent_file = file.read()
        book_upload.save()
        os.remove(torrent_temp_filename)

    return redirect('books-edit_upload', upload_id)


@login_required
def upload_to_what(request, upload_id):
    book_upload = BookUpload.objects.get(id=upload_id)
    what_upload.upload_to_what(request, book_upload)
    return redirect(request.GET['return'])


@login_required
def skip_what(request, upload_id):
    book_upload = BookUpload.objects.defer(*BookUpload.binary_fields).get(id=upload_id)
    book_upload.what_torrent_id = 0
    book_upload.save()
    return redirect('books-edit_upload', upload_id)


@login_required
def skip_bibliotik(request, upload_id):
    book_upload = BookUpload.objects.defer(*BookUpload.binary_fields).get(id=upload_id)
    book_upload.bibliotik_torrent_id = 0
    book_upload.save()
    return redirect('books-edit_upload', upload_id)
