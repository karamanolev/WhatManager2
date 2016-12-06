#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.db import transaction

from WhatManager2 import settings
from WhatManager2.management.commands import transmission_provision
from WhatManager2.management.commands.transmission_provision import TransInstanceManager, \
    ensure_root, confirm, ensure_replica_sets_exist, apply_options
from home import models


class Command(BaseCommand):
    BaseCommand.add_arguments(transmission_provision.Command.option_list)
    args = u'<zone_name>'
    help = u'Provisions transmission instances'

    def handle(self, *args, **options):
        apply_options(options)
        ensure_root()
        if len(args) != 1:
            print u'Pass only the zone name.'
            return 1
        zone = args[0]
        ensure_replica_sets_exist()
        replica_set = models.ReplicaSet.objects.get(zone=zone)
        old_instances = replica_set.transinstance_set.order_by('-port').all()
        if len(old_instances):
            old_instance = old_instances[0]
        else:
            if replica_set.zone == models.ReplicaSet.ZONE_WHAT:
                zero_port = 9090
                zero_peer_port = 21412
            elif replica_set.zone == models.ReplicaSet.ZONE_BIBLIOTIK:
                zero_port = 10090
                zero_peer_port = 22412
            elif replica_set.zone == models.ReplicaSet.ZONE_MYANONAMOUSE:
                zero_port = 11090
                zero_peer_port = 23412
            else:
                raise Exception('Unknown zone')
            old_instance = models.TransInstance(
                replica_set=replica_set,
                name=u'{0}00'.format(replica_set.zone
                                     .replace('.cd', '')
                                     .replace('.org', '')
                                     .replace('.net', '')
                                     .replace('.me', '')),
                host='127.0.0.1',
                port=zero_port,
                peer_port=zero_peer_port,
                username='transmission',
                password=settings.TRANSMISSION_PASSWORD,
            )
        new_instance = models.TransInstance(
            replica_set=old_instance.replica_set,
            name=u'{0}{1:02}'.format(old_instance.name[:-2], int(old_instance.name[-2:]) + 1),
            host=old_instance.host,
            port=old_instance.port + 1,
            peer_port=old_instance.peer_port + 1,
            username=old_instance.username,
            password=settings.TRANSMISSION_PASSWORD,
        )
        print new_instance.full_description()
        print u'Is this OK?'
        confirm()
        with transaction.atomic():
            instance_manager = TransInstanceManager(new_instance)
            instance_manager.sync()
            new_instance.save()

        print 'Starting daemon...'
        instance_manager.start_daemon()

        print u'Instance synced and saved.'
