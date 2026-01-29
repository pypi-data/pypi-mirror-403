import datetime
import logging
from datetime import timezone
from enum import IntFlag

from django.contrib.humanize.templatetags.humanize import intcomma, naturaltime
from django.db import models
from django.db.models import CharField, DateTimeField, GenericIPAddressField, IntegerField, TextField
from django.utils import timezone as utils_timezone
from django_enum import EnumField

from .apps import Config

logger = logging.getLogger(__name__)


class HttpMethod(IntFlag):
    CONNECT = 1
    DELETE = 2
    GET = 4
    HEAD = 8
    OPTIONS = 16
    PATCH = 32
    POST = 64
    PUT = 128
    TRACE = 256


class BlockedIP(models.Model):
    ip = GenericIPAddressField(primary_key=True, verbose_name="IP")

    allowed_methods: EnumField = EnumField(
        HttpMethod, default=0, help_text="HTTP methods that this IP can use"
    )
    cooldown = IntegerField(
        default=Config.defaults["cooldown"],
        help_text="Cooldown period; number of days with no connections before IP is dropped from blocklist",
    )
    datetime_added = DateTimeField(default=utils_timezone.now, db_index=True)
    internal_notes = TextField(blank=True, null=True)
    last_seen = DateTimeField(blank=True, null=True, db_index=True)
    reason = CharField(blank=True, max_length=255, default="", db_index=True)
    tally = IntegerField(default=0, help_text="Number of times this IP has been blocked since datetime_added")

    class Meta:
        get_latest_by = "datetime_added"
        ordering = ["-last_seen", "-datetime_added", "ip"]
        verbose_name = "blocked IP"

    def __str__(self) -> str:
        return self.ip

    def verbose_str(self):
        timespan = naturaltime(self.datetime_added).replace(" ago", "")
        return (
            f"{self.ip}"
            + f" -- {intcomma(self.tally)} blocks in {timespan}"
            + (f" -- seen {naturaltime(self.last_seen)}" if self.last_seen else "")
            + f" -- {self.cooldown} day cooldown"
            + f"{' -- ' + self.reason if self.reason else ''}"
            + f"{' -- Allowed ' + self.allowed_methods_str() if self.allowed_methods else ''}"
        )

    def allowed_methods_str(self):
        return BlockedIP.method_intflag_to_names(self.allowed_methods)

    def has_expired(self):
        """Has the IP cooled long enough to be removed from the list?"""
        quiet_time = datetime.datetime.now(timezone.utc) - (self.last_seen or self.datetime_added)
        return quiet_time.days >= self.cooldown

    @classmethod
    def method_names_to_intflag(_, method_string) -> int:
        """Convert e.g. 'HEAD,GET' to 12 (bitfield format. Returns 0 if no valid method names found. Case insensitive."""
        allowed_methods_intflag = 0
        for method in method_string.split(","):
            enum_member = getattr(HttpMethod, method.upper(), None)
            if enum_member is None:
                logger.error(f"Can't convert unknown HTTP method '{method}', skipping")
            else:
                allowed_methods_intflag |= enum_member
        return allowed_methods_intflag

    @classmethod
    def method_intflag_to_names(_, method_intflag: int) -> str:
        """Convert e.g. 12 (bitfield format) to 'GET,HEAD'"""
        return ",".join(str(method.name) for method in HttpMethod if method_intflag & method)
