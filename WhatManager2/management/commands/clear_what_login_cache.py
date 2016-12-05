from django.core.management.base import BaseCommand

from home.models import WhatLoginCache

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        
        WhatLoginCache.objects.all().delete()