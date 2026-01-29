"""Update blocklist with new IPs, or set metadata on existing IPs."""

import logging

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import validate_ipv46_address

from ...models import BlockedIP
from ...utils import COOLDOWN

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("ips", nargs="+", type=str, help="IPs (space-separated)")
        parser.add_argument(
            "--cooldown",
            help=f"Days with no requests before IP is dropped from blocklist (default: {COOLDOWN})",
        )
        parser.add_argument("--reason", help="'reason' field value for these IPs", default="")
        parser.add_argument(
            "--allowed_methods", help="Comma-separated list of HTTP methods not to block", default=""
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Don't alter records for any IPs already in the DB",
            default="",
        )

    help = __doc__

    def handle(self, *args, **options):
        allowed_methods = options.get("allowed_methods")
        cooldown = options.get("cooldown")
        ips = options.get("ips")
        reason = options.get("reason")
        skip_existing = options.get("skip_existing")

        added_count = updated_count = skipped_count = unchanged_count = invalid_count = 0
        for ip in ips:
            try:
                validate_ipv46_address(ip)
            except ValidationError:
                print(f"Invalid IP: {ip}")
                invalid_count += 1
                continue
            entry, created = BlockedIP.objects.get_or_create(ip=ip)
            if not created and skip_existing:
                print(f"{ip} already present; skipping")
                skipped_count += 1
                continue
            updated_fields = []
            if allowed_methods:
                methods_intflag = BlockedIP.method_csv_to_intflag(allowed_methods)
                if entry.allowed_methods != allowed_methods:
                    entry.allowed_methods = methods_intflag
                    updated_fields.append("allowed_methods")
            if cooldown and entry.cooldown != (cooldown := int(cooldown)):
                entry.cooldown = cooldown
                updated_fields.append("cooldown")
            if reason and entry.reason != reason:
                entry.reason = reason
                updated_fields.append("reason")
            if updated_fields or created:
                entry.save()
                summary = "Created entry" if created else f"Updated {' and '.join(updated_fields)}"
                print(f"{summary} for {ip}")
            if created:
                added_count += 1
            elif updated_fields:
                updated_count += 1
            else:
                unchanged_count += 1
        print(
            f"\nSummary:\n{added_count=}\n{updated_count=}\n{skipped_count=}\n{unchanged_count=}\n{invalid_count=}"
        )
