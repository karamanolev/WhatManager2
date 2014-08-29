#!/usr/bin/env python

import os

from django.core.management.base import BaseCommand, CommandError

from WhatManager2.management.commands.transmission_provision import TransInstanceManager
from home import models


class Command(BaseCommand):
    help = 'Provisions transmission instances'

    def handle(self, *args, **options):
        if os.geteuid() != 0:
            raise CommandError('You have to call this program as root.')
        for instance in models.TransInstance.objects.order_by('name'):
            manager = TransInstanceManager(instance)
            manager.stop_daemon()
