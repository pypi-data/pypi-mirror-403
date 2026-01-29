import datetime
from datetime import timezone
from typing import Callable

from django.contrib import admin, messages

from .models import BlockedIP, HttpMethod


@admin.display(description="Reason")
def reason_truncated(entry: BlockedIP) -> str:
    return entry.reason[:20] + ("..." if len(entry.reason) > 20 else "")


@admin.display(description="Cooldown")
def cooldown(entry: BlockedIP) -> str:
    return f"{entry.cooldown} days"


@admin.display(description="Allowed Methods")
def allowed_methods(entry: BlockedIP) -> str:
    if entry.allowed_methods == 0:
        return "NONE"
    else:
        return BlockedIP.method_intflag_to_names(entry.allowed_methods)


@admin.display(description="Days left")
def days_left(entry: BlockedIP) -> str:
    remaining = f"{entry.cooldown - (datetime.datetime.now(timezone.utc) - (entry.last_seen or entry.datetime_added)).days}"
    return remaining

# Helper for dynamically building allowed-method toggle actions (called from get_actions)
def create_allowed_method_toggle_fn(method: HttpMethod) -> Callable:
    def toggle_method(_modeladmin, request, queryset):
        for entry in queryset:
            entry.allowed_methods ^= method.value
            entry.save()
        messages.success( request, f"Toggled { method.name } on {queryset.count()} entries", fail_silently=True)
    toggle_method.__name__ = f"toggle_{ method.name }"
    return toggle_method


class AllowedMethodsFilter(admin.SimpleListFilter):
    title = "Allowed methods"
    parameter_name = "allowed_methods_filter"

    def lookups(self, request, model_admin):
        return [(method.value, f"Allows {method.name}") for method in HttpMethod]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(allowed_methods__has_any=self.value())
        return queryset


class BlockedIPAdmin(admin.ModelAdmin):
    list_display = [
        "ip",
        "datetime_added",
        "last_seen",
        "tally",
        cooldown,
        days_left,
        allowed_methods,
        reason_truncated,
    ]
    list_filter = [
        "cooldown",
        "datetime_added",
        "last_seen",
        "reason",
        AllowedMethodsFilter,
    ]
    search_fields = ["ip", "reason"]

    class Meta:
        model = BlockedIP

    def get_actions(self, request):
        """Programmatically add a toggle function (action) for each HTTP method"""
        actions = super().get_actions(request)
        # Generate helper functions
        for method in HttpMethod:
            fn = create_allowed_method_toggle_fn(method)
            actions[fn.__name__] = (fn, fn.__name__, f"Toggle { method.name } in allowed_methods")
        return actions

admin.site.register(BlockedIP, BlockedIPAdmin)
