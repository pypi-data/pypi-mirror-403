"""Look up provided IPs in the blocklist. Set --verbosity=2 to see full record for found IPs."""

import logging
import sys

from django.core.management.base import BaseCommand

from ...models import BlockedIP

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("ips", nargs="+", type=str, help="IPs to look up (space separated)")

    def handle(self, *args, **options):
        ips = options.get("ips")
        self.verbosity = options.get("verbosity", 1)
        for entry in BlockedIP.objects.filter(ip__in=ips):
            print(entry.verbose_str() if self.verbosity >= 2 else f"Found: {entry.ip}")
        if self.verbosity > 1:
            not_found = " ".join(ip for ip in ips if not BlockedIP.objects.filter(ip=ip).exists())
            if not_found.strip():
                print(f"Not found: {not_found}")
                sys.exit(1)
