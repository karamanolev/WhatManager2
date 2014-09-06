from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fixes missing entries in what_meta by iterating `WhatTorrent`s.'

    def handle(self, *args, **options):
        pass
