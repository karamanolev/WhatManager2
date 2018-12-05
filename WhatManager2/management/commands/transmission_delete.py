#!/usr/bin/env python
from django.core.management.base import BaseCommand, CommandError

from WhatManager2.management.commands.transmission_provision import confirm, TransInstanceManager, ensure_root
from home.models import TransInstance


class Command(BaseCommand):
    help = 'Removes existing Transmission instances'

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='+')

    def handle(self, *args, **options):
        ensure_root()
        for name in options['name']:
            try:
                instance = TransInstance.objects.get(name=name)
            except TransInstance.DoesNotExist:
                raise CommandError('TransInstance "%s" does not exist' % name)

            if instance.torrent_count > 0:
                # Don't allow instances with torrents to be deleted for now. Would be more complicated, destructive and
                # less likely for users to want to do so anyway.
                self.stdout.write(self.style.WARNING('Will not delete "%s", as it contains torrents' % instance.name))
                return

            print('Deleting TransInstance %s...' % instance.name)
            self.stdout.write(self.style.NOTICE('This will remove the daemon, all related files, and the user.'))
            confirm()

            manager = TransInstanceManager(instance)
            manager.remove()

            instance.delete()

            # BaseCommand.style.SUCCESS was only added in Django 1.9
            if hasattr(self.style, 'SUCCESS'):
                self.stdout.write(self.style.SUCCESS('Successfully deleted "%s"' % instance.name))
            else:
                self.stdout.write(self.style.WARNING('Successfully deleted "%s"' % instance.name))
