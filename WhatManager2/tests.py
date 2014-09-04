from django.test.testcases import TestCase
from mock import patch

from WhatManager2.management.commands import transmission_provision


@patch('WhatManager2.management.commands.transmission_provision.confirm')
class ProvisioningTests(TestCase):
    def test_ensure_replica_sets_exist(self, mock_confirm):
        transmission_provision.ensure_replica_sets_exist()
        self.assertEqual(transmission_provision.confirm.call_count, 2)
