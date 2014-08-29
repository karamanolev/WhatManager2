#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.db import transaction

from WhatManager2 import settings

from WhatManager2.management.commands.transmission_provision import TransInstanceManager, ensure_root
from home import models


def confirm():
    answer = raw_input('Enter y to continue: ')
    if answer != 'y':
        exit(1)


class Command(BaseCommand):
    args = u'<zone_name>'
    help = u'Provisions transmission instances'

    def handle(self, *args, **options):
        ensure_root()
        if len(args) != 1:
            print u'Pass only the zone name.'
            return
        zone = args[0]
        try:
            replica_set = models.ReplicaSet.objects.get(zone=zone)
        except models.ReplicaSet.DoesNotExist:
            print u'There is no replica set with the name {0}. I will create one.'.format(args[0])
            confirm()
            replica_set = models.ReplicaSet(
                zone=zone,
                name='master',
            )
            replica_set.save()
        old_instances = replica_set.transinstance_set.order_by('-port').all()
        if len(old_instances):
            old_instance = old_instances[0]
        else:
            old_instance = models.TransInstance(
                replica_set=replica_set,
                name=u'{0}00'.format(replica_set.zone),
                host='127.0.0.1',
                port=9090,
                peer_port=51412,
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
            password=old_instance.password,
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
