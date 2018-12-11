# Create your views here.
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import render, redirect

from WhatManager2.utils import get_user_token


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                if 'next' in request.GET:
                    return redirect(request.GET['next'])
                else:
                    return redirect('home:dashboard')
    else:
        username = ''
        password = ''
    data = {
        username: username,
        password: password
    }
    return render(request, 'login/login.html', data)


def logout(request):
    auth.logout(request)
    return redirect('home:dashboard')


@login_required
def view_token(request):
    return HttpResponse(get_user_token(request.user))
