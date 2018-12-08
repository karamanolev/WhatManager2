from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    data = {
    }
    return render(request, 'wmqueue/queue.html', data)
