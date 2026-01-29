"""
Print blocked IPs to stdout.

IPs are printed one per line. Use --json to print a JSON array. Use --reason to
filter to only BlockedIP objects whose `reason` field exactly matches the
provided string.
"""

import json

from django.core.management.base import BaseCommand

from ...models import BlockedIP


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Output JSON array of IPs")
        parser.add_argument("--plain", action="store_true", help="Output one IP per line (plain text)")
        parser.add_argument("--reason", help="Filter to BlockedIP objects whose `reason` equals this string")

    def handle(self, *args, **options):
        queryset = BlockedIP.objects.all()
        if reason := options.get("reason"):
            queryset = queryset.filter(reason=reason)

        ips = [entry.ip for entry in queryset.order_by("ip")]

        if options.get("json"):
            print(json.dumps(ips))
        else:
            for ip in ips:
                print(ip)
