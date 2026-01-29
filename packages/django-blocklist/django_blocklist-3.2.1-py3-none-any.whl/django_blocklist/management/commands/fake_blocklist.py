"""Generate fake blocklist entries for testing. Only generates non-routable IPs."""

import datetime
import sys
from datetime import timezone
from random import randint

from django.core.management.base import BaseCommand

from ...models import BlockedIP


def random_fake_ip() -> str:
    template = "192.168.{}.{}"
    return template.format(randint(0, 255), randint(0, 255))


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--quantity", type=int, default=10, help="Number of fake IPs to generate")

    def handle(self, *args, **options):
        if (quantity := options.get("quantity")) > (max := 256**2):
            sys.exit(f"Can't generate more than {max}, sorry.")
        while quantity:
            entry, created = BlockedIP.objects.get_or_create(ip=random_fake_ip())
            if created:
                entry.tally = randint(1, 100)
                entry.reason = f"Fake reason {randint(1, 3)}"
                entry.datetime_added = datetime.datetime.now(timezone.utc) - datetime.timedelta(
                    randint(1, 10)
                )
                entry.last_seen = entry.datetime_added + datetime.timedelta(
                    days=randint(1, entry.cooldown - 1)
                )
                entry.save()
                quantity -= 1
        print(f"Generated {options.get('quantity')} BlockedIP entries.")
