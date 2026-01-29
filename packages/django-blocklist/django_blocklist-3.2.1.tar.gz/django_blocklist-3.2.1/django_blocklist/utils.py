import logging
from datetime import datetime
from itertools import chain
from typing import Optional

from django.conf import settings
from django.http import HttpRequest

from .apps import Config
from .models import BlockedIP, HttpMethod

logger = logging.getLogger(__name__)
BLOCKLIST_CACHE_KEY = "django-blocklist-ips"
COOLDOWN = settings.BLOCKLIST_CONFIG.get("cooldown", Config.defaults["cooldown"])


def user_ip_from_request(request: HttpRequest) -> str:
    """Returns user's IP. If IP can't be determined, return empty string and log a warning."""
    # Hat-tip to django-ipware for header list: https://github.com/un33k/django-ipware/
    headers = [
        "CF-CONNECTING-IP",  # CloudFlare
        "CLIENT-IP",  # Akamai and Cloudflare: True-Client-IP and Fastly: Fastly-Client-IP
        "FASTLY-CLIENT-IP",  # Firebase, Fastly
        "FORWARDED_FOR",  # RFC 7239
        "FORWARDED",  # RFC 7239
        "HTTP_CF_CONNECTING_IP",  # CloudFlare
        "HTTP_CLIENT_IP",  # Standard headers used by providers such as Amazon EC2, Heroku etc.
        "HTTP_FORWARDED_FOR",  # RFC 7239
        "HTTP_FORWARDED",  # RFC 7239
        "HTTP_X_CLUSTER_CLIENT_IP",  # Rackspace LB and Riverbed Stingray
        "HTTP_X_FORWARDED_FOR",  # Similar to X_FORWARDED_TO
        "HTTP_X_FORWARDED",  # Squid and others
        "HTTP_X_REAL_IP",  # Standard headers used by providers such as Amazon EC2, Heroku etc.
        "REMOTE_ADDR",  # Default
        "TRUE-CLIENT-IP",  # CloudFlare Enterprise
        "X_FORWARDED_FOR",  # Load balancers or proxies such as AWS ELB (default client is left-most)
        "X_FORWARDED",  # Squid
        "X-CLIENT-IP",  # Microsoft Azure
        "X-CLUSTER-CLIENT-IP",  # Rackspace Cloud Load Balancers
        "X-REAL-IP",  # NGINX
    ]
    for header in headers:
        if ip := request.META.get(header):
            if "," in str(ip):
                ip = str(ip).strip(",").split(",")[0]
            return ip
    logger.error("No IP address could be found in request headers: {}".format(request.META))
    return ""


def blocked_methods_for_ip(ip: str) -> set:
    try:
        record = BlockedIP.objects.get(ip=ip)
        return set(HttpMethod) - set(record.allowed_methods)
    except BlockedIP.DoesNotExist:
        return set()


def should_block(request: HttpRequest) -> bool:
    """
    Return True if the requesting IP is valid and in the blocklist, 
    unless request's HTTP method is explicitly allowed.
    """
    # If IP has no record (or isn't valid), we don't block.
    try:
        record = BlockedIP.objects.get(ip=user_ip_from_request(request))
    except (ValueError, BlockedIP.DoesNotExist):
        return False
    # IP has a record; if request.method is not in its `allowed_methods`, block.
    try:
        method_enum = getattr(HttpMethod, str(request.method))
    except AttributeError:
        logger.error(f"Unknown method '{request.method}")
        return False
    return method_enum not in record.allowed_methods


def update_blocklist(
    ips: set,
    reason="",
    cooldown: Optional[int] = None,
    last_seen: Optional[datetime] = None,
    skip_existing: bool = True,
) -> None:
    """
    Add the provided IPs to the blocklist, with optional `reason` and `cooldown`.
    Set `skip_existing=False` to update existing IPs; by default, they will be left alone.
    Refreshes the cache when complete.
    """
    if cooldown is None:
        cooldown = COOLDOWN
    skiplist = list(chain(*BlockedIP.objects.values_list("ip"))) if skip_existing else []
    for ip in ips:
        if skip_existing and ip in skiplist:
            logger.info(f"Skipping {ip}, already present")
            continue
        else:
            entry, new = BlockedIP.objects.get_or_create(ip=ip)
        entry.reason = reason
        entry.cooldown = cooldown
        entry.last_seen = last_seen
        entry.save()
        if new:
            logger.info(f"Added blocklist entry: {ip}, {reason=} {cooldown=}")
        else:
            logger.info(f"Updated blocklist entry for {ip}: {reason=} {cooldown=}")


def remove_from_blocklist(ip: str) -> bool:
    """Remove the IP from the blocklist. Return True if successful, False if it wasn't found."""
    try:
        BlockedIP.objects.get(ip=ip).delete()
        return True
    except BlockedIP.DoesNotExist:
        logger.warning(f"Removal of {ip} requested, but not found in blocklist.")
        return False
