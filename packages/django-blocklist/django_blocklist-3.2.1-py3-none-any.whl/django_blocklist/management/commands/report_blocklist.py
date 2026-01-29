"""Print summary information about the data in the blocklist."""

import datetime
from collections import Counter
from datetime import timezone
from operator import itemgetter
from typing import Iterable, Tuple

from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from ...models import BlockedIP


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--reason",
            default=[],
            action="append",
            help="Restrict report to IPs with this reason (muliple reasons can be passed)",
        )
        parser.add_argument(
            "--methods",
            default="",
            help="Comma-separated list. Include entries whose `allowed_methods` includes one more more of these.",
        )

    help = __doc__

    def handle(self, *args, **options):
        entries = BlockedIP.objects.all()
        if selected_reasons := options.get("reason"):
            entries = entries.filter(reason__in=selected_reasons)
        if methods := BlockedIP.method_names_to_intflag(options.get("methods")):
            entries = entries.filter(allowed_methods__has_any=methods)
        if entries.count() == 0:
            raise CommandError("No BlockedIP objects for report.")
        _grand_tally = entries.aggregate(Sum("tally"))["tally__sum"]
        print(f"Total blocks of listed IPs: {intcomma(_grand_tally)}")
        print(f"Entries in blocklist: {intcomma(entries.count())}")
        _one_day_ago = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=1)
        print(f"Active in last 24 hours: {intcomma(entries.filter(last_seen__gte=_one_day_ago).count())}")
        print(
            f"Stale (added over 24h ago, not seen since): {intcomma(entries.filter(tally=0, last_seen__lt=_one_day_ago).count())}"
        )
        print()
        print_roster("Most recent", entries.exclude(tally=0).order_by("-last_seen")[:5])
        print_roster("Most active", entries.filter(tally__gt=0).order_by("-tally"), activity_calc=True)
        # Find longest-lived
        longest_lived = None
        how_long = datetime.timedelta(0)
        for entry in entries:
            active_period = (entry.last_seen or entry.datetime_added) - entry.datetime_added
            if active_period > how_long:
                longest_lived, how_long = entry, active_period
        if longest_lived is not None:
            print(f"Longest lived:\n{longest_lived.verbose_str()}")
        if stats := reason_stats():
            print(f"\n{'Reason':30}  {'Seen':7}   {'Listed':7}   {'Tally':9}\n" + "-" * 62)
            total_seen = total_ips = total_tally = 0
            for reason, seen_count, ip_count, tally in stats:
                if not selected_reasons or reason in selected_reasons:
                    print(f"{reason:<30.30} | {seen_count:7,} | {ip_count:7,} | {tally:9,}")
                    total_seen += seen_count
                    total_ips += ip_count
                    total_tally += tally
            print("-" * 62)
            print(f"(Totals)                       | {total_seen:7,} | {total_ips:7,} | {total_tally:9,}")


def print_roster(title: str, queryset, activity_calc: bool = False) -> None:
    print(f"{title}:")
    activity = {}
    for perp in queryset:
        # For each IP, either print a line or calculate the rate, depending on activity_calc
        if activity_calc:
            days = max(1, (datetime.datetime.now(timezone.utc) - perp.datetime_added).days)
            per_hour = perp.tally / days / 24
            activity[perp] = per_hour
        else:
            print(perp.verbose_str())
    if activity_calc:
        most_active = sorted(activity.items(), key=itemgetter(1), reverse=True)[:5]
        for perp, per_hour in most_active:
            if round(per_hour) > 0:
                print(f"{perp.verbose_str()} -- {round(per_hour)} per hour")
    print()


def reason_stats() -> Iterable[Tuple[str, int, int, int]]:
    """Gather ip-count and grand tally stats for each reason"""
    stats = Counter(BlockedIP.objects.exclude(reason="").values_list("reason"))
    tuples = []
    for reason_datum in stats.items():
        reason = str(reason_datum[0][0])
        ip_count = reason_datum[1]
        tally = BlockedIP.objects.filter(reason=reason).aggregate(tally=Sum("tally"))["tally"]
        seen_count = BlockedIP.objects.filter(reason=reason, tally__gt=0).count()
        tuples.append((reason, seen_count, ip_count, tally))
    return sorted(tuples, key=itemgetter(1), reverse=True)
