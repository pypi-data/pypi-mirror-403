from django.core.cache import cache
from django.db.utils import IntegrityError
from django.http import HttpRequest
from django.test import TestCase

from ..models import BlockedIP, HttpMethod
from ..utils import (
    BLOCKLIST_CACHE_KEY,
    COOLDOWN,
    remove_from_blocklist,
    should_block,
    update_blocklist,
    user_ip_from_request,
)


class UtilsTests(TestCase):
    def setUp(self):
        cache.delete(BLOCKLIST_CACHE_KEY)

    def tearDown(self):
        cache.delete(BLOCKLIST_CACHE_KEY)

    def test_update_blocklist(self):
        ips = {"2.2.2.2", "3.3.3.3"}
        update_blocklist(ips)
        result = {bi.ip for bi in BlockedIP.objects.all()}
        self.assertEqual(result, ips)

    def test_update_blocklist_skipping_existing(self):
        BlockedIP.objects.create(ip="2.2.2.2", reason="OLD")
        update_blocklist({"2.2.2.2", "3.3.3.3"}, reason="NEW")
        assert BlockedIP.objects.get(ip="2.2.2.2").reason == "OLD"
        assert BlockedIP.objects.get(ip="3.3.3.3").reason == "NEW"

    def test_update_blocklist_defaults_and_params(self):
        update_blocklist(set(["4.4.4.4"]))
        blocked = BlockedIP.objects.get(ip="4.4.4.4")
        self.assertEqual(blocked.reason, "")
        self.assertEqual(blocked.cooldown, COOLDOWN)
        update_blocklist(
            set(["5.5.5.5"]), reason=(expected_reason := "TOS"), cooldown=(expected_cooldown := 99)
        )
        blocked = BlockedIP.objects.get(ip="5.5.5.5")
        self.assertEqual(blocked.reason, expected_reason)
        self.assertEqual(blocked.cooldown, expected_cooldown)

    def test_add_duplicate(self):
        ip = "9.9.9.9"
        update_blocklist(ip)
        try:
            update_blocklist(ip)
        except IntegrityError:
            self.fail("update_blocklist failed to handle duplicate IP")

    def test_remove(self):
        ip = "1.1.1.1"
        BlockedIP.objects.create(ip=ip)
        assert BlockedIP.objects.filter(ip=ip).exists()
        remove_from_blocklist([ip])
        assert not BlockedIP.objects.filter(ip__in=ip).exists()

    def test_helper__user_ip_from_request(self):
        request = HttpRequest()
        headers = "CF-CONNECTING-IP CLIENT-IP FASTLY-CLIENT-IP HTTP_CF_CONNECTING_IP HTTP_CLIENT_IP HTTP_X_CLUSTER_CLIENT_IP HTTP_X_REAL_IP REMOTE_ADDR TRUE-CLIENT-IP X-CLIENT-IP X-CLUSTER-CLIENT-IP X-REAL-IP".split()
        for header in headers:
            request.META[header] = (ip := "11.12.13.14")
            assert user_ip_from_request(request) == ip, f"{header} check failed"
            del request.META[header]

    def test_helper__user_ip_from_request__forwarding(self):
        request = HttpRequest()
        headers = "FORWARDED FORWARDED_FOR HTTP_FORWARDED HTTP_FORWARDED_FOR HTTP_X_FORWARDED HTTP_X_FORWARDED_FOR X_FORWARDED X_FORWARDED_FOR".split()
        for header in headers:
            ip = "11.12.13.14"
            request.META[header] = f"{ip},11.12.13.15"
            assert user_ip_from_request(request) == ip, f"{header} check failed"
            request.META[header] = "11.12.13.14,"
            assert user_ip_from_request(request) == ip, f"{header} check failed"
            del request.META[header]

    def test_should_block(self):
        request = HttpRequest()
        request.META["REMOTE_ADDR"] = (ip := "1.1.1.1")
        request.method = "GET"
        BlockedIP.objects.create(ip=ip, allowed_methods=HttpMethod.GET)
        assert should_block(request) is False
        request.method = "POST"
        assert should_block(request) is True
