from home.models import DownloadLocation


def context_processor(request):
    return {
        'locations': DownloadLocation.objects.filter()
    }
