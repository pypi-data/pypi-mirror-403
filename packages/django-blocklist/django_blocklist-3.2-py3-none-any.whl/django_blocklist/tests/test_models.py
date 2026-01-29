import datetime
import pytest
import unittest
from datetime import timezone

from ..models import BlockedIP, HttpMethod


@pytest.mark.django_db
class DateTests(unittest.TestCase):
    def setUp(self):
        BlockedIP.objects.all().delete()
        self.ip = "1.1.1.1"

    def test_days_left(self):
        two_days_ago = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=2)
        BlockedIP.objects.create(ip=self.ip, cooldown=3, last_seen=two_days_ago)
        entry = BlockedIP.objects.get(ip=self.ip)
        remaining = entry.cooldown - (datetime.datetime.now(timezone.utc) - entry.last_seen).days
        self.assertEqual(remaining, 1)

    def test_last_seen_not_auto_set(self):
        b = BlockedIP.objects.create(ip=self.ip)
        self.assertIs(b.last_seen, None)


@pytest.mark.django_db
class AllowedMethodTests(unittest.TestCase):
    def setUp(self):
        BlockedIP.objects.all().delete()
        self.ip = "2.2.2.2"

    def test_allow_none(self):
        """By default, no methods should be allowed"""
        b = BlockedIP.objects.create(ip=self.ip)
        for method in HttpMethod:
            assert not (method & b.allowed_methods)

    def test_allow_all(self):
        b = BlockedIP.objects.create(ip=self.ip, allowed_methods=~0)
        for method in HttpMethod:
            assert method & b.allowed_methods

    def test_allow_only_get_and_head(self):
        b = BlockedIP.objects.create(ip=self.ip, allowed_methods=HttpMethod.GET | HttpMethod.HEAD)
        assert HttpMethod.GET & b.allowed_methods
        assert HttpMethod.HEAD & b.allowed_methods
        assert not (HttpMethod.POST & b.allowed_methods)

    def test_str_method(self):
        """Confirm that `allowed_methods_str` renders method names, and uses the enum's order"""
        b = BlockedIP.objects.create(ip=self.ip, allowed_methods=HttpMethod.OPTIONS | HttpMethod.CONNECT)
        assert b.allowed_methods_str() == "CONNECT,OPTIONS"

    def test_convert_between_http_method_names_and_flags(self):
        intflag = HttpMethod.GET | HttpMethod.DELETE | HttpMethod.CONNECT
        assert BlockedIP.method_intflag_to_names(intflag) == "CONNECT,DELETE,GET"
        assert BlockedIP.method_names_to_intflag("CONNECT,DELETE,GET") == intflag
