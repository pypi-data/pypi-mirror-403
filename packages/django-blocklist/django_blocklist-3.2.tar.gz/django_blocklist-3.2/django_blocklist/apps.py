from django.apps import AppConfig


class Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_blocklist"
    # These can be overridden via settings.BLOCKLIST_CONFIG
    defaults = {
        "cooldown": 7,
        "denial-template": "Your IP address {ip} has been blocked. Try again in {cooldown} days.",
    }
