from datetime import timezone
import datetime
import pytest
import sys
import unittest
from django.core.management import call_command
from io import StringIO

from ..models import BlockedIP


@pytest.mark.django_db
class CommandsTest(unittest.TestCase):
    def setUp(self):
        BlockedIP.objects.all().delete()
        self.ip1 = "1.1.1.1"
        self.ip2 = "2.2.2.2"

    def tearDown(self):
        BlockedIP.objects.all().delete()

    def test_clean(self):
        two_days_ago = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=2)
        BlockedIP.objects.create(ip=self.ip1, cooldown=1, last_seen=two_days_ago)
        BlockedIP.objects.create(ip=self.ip2, cooldown=3, last_seen=two_days_ago)
        assert BlockedIP.objects.count() == 2
        # Running clean_blocklist with --dry-run doesn't delete one
        call_command("clean_blocklist", verbosity=0, dry_run=1)
        self.assertEqual(BlockedIP.objects.count(), 2)
        # Running clean_blocklist _does_ delete one
        call_command("clean_blocklist", verbosity=0)
        self.assertEqual(BlockedIP.objects.count(), 1)
        # The one that should still be there, is still there
        self.assertTrue(BlockedIP.objects.filter(ip=self.ip2).exists())

    def test_clean_with_no_last_seen(self):
        two_days_ago = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=2)
        # A never-seen IP that has satisfied its coolown
        BlockedIP.objects.create(ip=self.ip2, datetime_added=two_days_ago, cooldown=1)
        assert BlockedIP.objects.count() == 1
        # Running clean_blocklist deletes it
        call_command("clean_blocklist", verbosity=0)
        self.assertEqual(BlockedIP.objects.count(), 0)

    def test_add(self):
        call_command("update_blocklist", self.ip1, verbosity=0)
        self.assertTrue(BlockedIP.objects.filter(ip=self.ip1).exists())

    def test_remove(self):
        ip = "4.4.4.4"
        BlockedIP.objects.create(ip=ip)
        call_command("remove_from_blocklist", ip, verbosity=0)
        self.assertEqual(BlockedIP.objects.filter(ip=ip).count(), 0)

    def test_add_invalid(self):
        sys.stdout = (out := StringIO())
        bad_ip = "foo"
        call_command("update_blocklist", bad_ip, verbosity=0)
        self.assertIn("Invalid", out.getvalue())

    def test_update_changes_stored_values(self):
        BlockedIP.objects.create(ip=self.ip1, reason="R1", cooldown=1)
        call_command("update_blocklist", self.ip1, reason="R2", cooldown=2)
        entry = BlockedIP.objects.get(ip=self.ip1)
        self.assertEqual(entry.reason, "R2")
        self.assertEqual(entry.cooldown, 2)

    def test_update_creation_message(self):
        """Newly created entry should be reported"""
        sys.stdout = (out := StringIO())
        call_command("update_blocklist", self.ip1)
        self.assertIn("Created", out.getvalue())

    def test_update_output_names_changed_fields(self):
        """If we make updates, output should say so"""
        sys.stdout = (out := StringIO())
        BlockedIP.objects.create(ip=self.ip1, reason="R1", cooldown=1)
        call_command("update_blocklist", self.ip1, cooldown=2)
        self.assertIn("Updated cooldown for", out.getvalue())
        call_command("update_blocklist", self.ip1, reason="R2")
        self.assertIn("Updated reason for", out.getvalue())
        call_command("update_blocklist", self.ip1, reason="R3", cooldown=3)
        self.assertIn("Updated cooldown and reason", out.getvalue())

    def test_update_converts_cooldown_to_int(self):
        """Logic inside the update command needs cooldown to be cast to int"""
        sys.stdout = (out := StringIO())
        BlockedIP.objects.create(ip=self.ip1, cooldown=1)
        call_command("update_blocklist", self.ip1, cooldown="1")
        self.assertNotIn("Updated cooldown", out.getvalue())

    def test_update_no_message_if_no_change(self):
        """If we 'update' with the existing values, IP shouldn't show in output"""
        sys.stdout = (out := StringIO())
        BlockedIP.objects.create(ip=self.ip1, reason="R1", cooldown=1)
        call_command("update_blocklist", self.ip1, reason="R1", cooldown=1)
        self.assertNotIn(self.ip1, out.getvalue())

    def test_update_skip_existing(self):
        sys.stdout = (out := StringIO())
        BlockedIP.objects.create(ip=self.ip1, reason="R1", cooldown=1)
        call_command("update_blocklist", self.ip1, reason="R2", cooldown=2, skip_existing=True)
        # Confirm skipping was reported and original values are unchanged
        self.assertIn(f"{self.ip1} already present", out.getvalue())
        assert BlockedIP.objects.get(ip=self.ip1).reason == "R1"
        assert BlockedIP.objects.get(ip=self.ip1).cooldown == 1

    def test_report(self):
        sys.stdout = (out := StringIO())
        today = datetime.datetime.now(timezone.utc)
        yesterday = today - datetime.timedelta(days=1)
        BlockedIP.objects.create(ip=self.ip1, datetime_added=yesterday, last_seen=today)
        BlockedIP.objects.create(ip=self.ip2, datetime_added=yesterday, last_seen=today, tally=240)
        call_command("report_blocklist")
        result = out.getvalue()
        self.assertIn(f"{self.ip1} -- 0 blocks", result)
        self.assertIn("10 per hour", result)

    def test_reason_report(self):
        sys.stdout = (out := StringIO())
        reasons = ["A", "B"]
        for n, reason in enumerate(reasons):
            BlockedIP.objects.create(ip=f"{n}.{n}.{n}.{n}", reason=reason, tally=1)
        call_command("report_blocklist", reason="A")
        result = out.getvalue()
        assert BlockedIP.objects.count() == 2
        self.assertIn("Entries in blocklist: 1", result)
        self.assertIn(f"{'A':30} | {1:7} | {1:7} | {1:9}", result)
