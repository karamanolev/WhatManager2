from django.shortcuts import render

from WhatManager2.settings import USERSCRIPT_WM_ROOT


def bibliotik(request):
    data = {
        'root': USERSCRIPT_WM_ROOT
    }
    return render(request, 'userscript/bibliotik.user.js', data)


def whatcd(request):
    data = {
        'root': USERSCRIPT_WM_ROOT
    }
    return render(request, 'userscript/what.cd.user.js', data)


def overdrive(request):
    data = {
        'root': USERSCRIPT_WM_ROOT
    }
    return render(request, 'userscript/overdrive.user.js', data)
