from home.models import DownloadLocation, ReplicaSet


def context_processor(request):
    return {
        'locations': DownloadLocation.objects.filter()
    }