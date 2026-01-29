from datetime import timezone
import datetime

from django.core.cache import cache
from django.test import TestCase

from ..middleware import denial_template
from ..models import BlockedIP
from ..utils import BLOCKLIST_CACHE_KEY


class MiddlewareTests(TestCase):
    def setUp(self):
        BlockedIP.objects.all().delete()
        cache.delete(BLOCKLIST_CACHE_KEY)

    def tearDown(self):
        BlockedIP.objects.all().delete()
        cache.delete(BLOCKLIST_CACHE_KEY)

    def test_ip_block_hit(self):
        BlockedIP.objects.create(ip="127.0.0.1")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 400)

    def test_ip_block_message(self):
        entry = BlockedIP.objects.create(ip="127.0.0.1")
        response = self.client.get("/")
        expected = denial_template().format(ip=entry.ip, cooldown=entry.cooldown)
        self.assertTrue(expected in str(response.content))

    def test_ip_block_miss(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_update_last_seen(self):
        then = datetime.datetime(2020, 2, 29, tzinfo=timezone.utc)
        print(then)
        BlockedIP.objects.create(ip="127.0.0.1", datetime_added=then, last_seen=then, reason="last-seen test")
        self.client.get("/")
        self.assertGreater(BlockedIP.objects.get(reason="last-seen test").last_seen, then)

    def test_update_tally(self):
        BlockedIP.objects.create(ip="127.0.0.1")
        self.client.get("/")
        self.client.get("/")
        entry = BlockedIP.objects.get(ip="127.0.0.1")
        self.assertEqual(entry.tally, 2)
