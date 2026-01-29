from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from ..models import BlockedIP
from ..utils import BLOCKLIST_CACHE_KEY, update_blocklist


class SettingsTests(TestCase):
    def tearDown(self) -> None:
        BlockedIP.objects.all().delete()
        cache.delete(BLOCKLIST_CACHE_KEY)

    # override_settings doesn't work for this one, so we patch instead
    @patch("django_blocklist.utils.COOLDOWN", 11)
    def test_cooldown_setting(self):
        update_blocklist(["1.1.1.1"])
        blocked = BlockedIP.objects.get(ip="1.1.1.1")
        self.assertEqual(blocked.cooldown, 11)

    @override_settings(BLOCKLIST_CONFIG={"denial-template": "418"})
    def test_message_setting(self):
        update_blocklist(["127.0.0.1"])
        response = self.client.get("/")
        self.assertEqual(response.status_code, 400)
        self.assertIn(response.content, b"418")
