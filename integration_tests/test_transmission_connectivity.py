from django.test import testcases
from home.models import TransInstance


class TestTransmissionConnectivity(testcases.TestCase):
    def test_instances_connectible(self):
        for instance in TransInstance.objects.all():
            session_stats = instance.client.session_stats()
            self.assertTrue(type(session_stats.activeTorrentCount) is int)
