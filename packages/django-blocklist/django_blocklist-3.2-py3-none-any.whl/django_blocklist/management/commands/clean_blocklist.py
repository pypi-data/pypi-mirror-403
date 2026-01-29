"""Remove IPs from the blocklist if they have been inactive for the required cooldown."""

import datetime
import logging

from django.core.management.base import BaseCommand
from django.db.models import F
from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import DurationField
from django.db.models.query_utils import Q
from django.utils import timezone

from ...models import BlockedIP

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview the removal rather than performing it."
        )

    help = __doc__

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        self.verbosity = options.get("verbosity")
        total_at_start = BlockedIP.objects.count()

        if total_at_start == 0:
            self.handle_message("clean_blocklist found 0 BlockedIP entries")
            return
        # We create a reusable expression for calculating expiry
        cooldown_cutoff = timezone.now() - ExpressionWrapper(
            F("cooldown") * datetime.timedelta(days=1), output_field=DurationField()
        )
        # For IPs that have never ben seen, we measure cooldown since their datetime_added
        deletable = BlockedIP.objects.filter(
            Q(last_seen__lte=cooldown_cutoff) | Q(last_seen__isnull=True, datetime_added__lte=cooldown_cutoff)
        )
        if dry_run:
            message = f"Would have removed {deletable.count()} IPs."
        else:
            result = deletable.delete()
            message = f"Removed {result[0]} IPs from blocklist; {total_at_start - result[0]} remain."
            self.handle_message(message)

    def handle_message(self, message):
        logger.info(message)
        if self.verbosity > 0:
            print(message)
