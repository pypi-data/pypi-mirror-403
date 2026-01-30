from django import template
from django.contrib import admin
from django.conf import settings

register = template.Library()

# ================================
# DEFAULT THEME SETTINGS
# ================================
DEFAULT_SETTINGS = {
    "ENABLE_STATS": True,
    "STATS_LIMIT": 6,
    "STAT_SORT": "count_desc",  # or "alpha" by  default ascending
}

def get_setting(key):
    return getattr(settings, "COLDBLUE_SETTINGS", {}).get(
        key, DEFAULT_SETTINGS[key]
    )

# ================================
# BASE ICON MAP (GENERIC)
# ================================
BASE_ICON_MAP = {

    # PEOPLE / AUTH
    "user": "fa-user",
    "profile": "fa-id-badge",
    "account": "fa-user-circle",
    "customer": "fa-user-tie",
    "employee": "fa-user-gear",
    "member": "fa-user-check",
    "staff": "fa-user-shield",
    "group": "fa-users-gear",
    "role": "fa-user-lock",
    "permission": "fa-key",

    # COMMERCE
    "product": "fa-box",
    "item": "fa-cube",
    "order": "fa-cart-shopping",
    "invoice": "fa-file-invoice",
    "payment": "fa-credit-card",
    "transaction": "fa-money-bill-transfer",
    "subscription": "fa-repeat",
    "coupon": "fa-ticket",
    "discount": "fa-percent",

    # INVENTORY
    "stock": "fa-warehouse",
    "inventory": "fa-boxes-stacked",
    "shipment": "fa-truck",
    "delivery": "fa-truck-fast",
    "supplier": "fa-industry",
    "vendor": "fa-store",

    # CONTENT / CMS
    "post": "fa-pen-nib",
    "blog": "fa-blog",
    "article": "fa-newspaper",
    "page": "fa-file-lines",
    "comment": "fa-comments",
    "review": "fa-star",
    "media": "fa-photo-film",
    "image": "fa-image",
    "video": "fa-video",

    # TAXONOMY
    "category": "fa-tags",
    "tag": "fa-tag",
    "collection": "fa-folder-tree",

    # EDUCATION
    "course": "fa-graduation-cap",
    "lesson": "fa-book-open",
    "student": "fa-user-graduate",
    "teacher": "fa-chalkboard-user",
    "exam": "fa-file-pen",

    # SUPPORT
    "ticket": "fa-life-ring",
    "support": "fa-headset",
    "message": "fa-envelope",
    "notification": "fa-bell",
    "feedback": "fa-comment-dots",

    # SYSTEM
    "setting": "fa-gear",
    "config": "fa-sliders",
    "log": "fa-list",
    "report": "fa-chart-line",
    "analytics": "fa-chart-pie",

    # FILES
    "file": "fa-file",
    "document": "fa-file-lines",
    "upload": "fa-upload",
    "download": "fa-download",

    # FALLBACK
    "default": "fa-database",
}

# ================================
# ICON RESOLVER (WITH USER OVERRIDE)
# ================================
def resolve_icon(model_name):
    user_icons = getattr(settings, "COLDBLUE_ICON_OVERRIDES", {})
    return (
        user_icons.get(model_name)
        or BASE_ICON_MAP.get(model_name)
        or BASE_ICON_MAP["default"]
    )

# ================================
# STATS TEMPLATE TAG
# ================================
@register.inclusion_tag("admin/coldblue_stats.html", takes_context=True)
def coldblue_stats(context):
    request = context["request"]

    # Staff only
    if not request.user.is_staff:
        return {"stats": []}

    # Allow user to disable stats
    if not get_setting("ENABLE_STATS"):
        return {"stats": []}

    stats = []

    for model, model_admin in admin.site._registry.items():

        # Respect admin permissions
        if not (
            model_admin.has_view_permission(request)
            or model_admin.has_change_permission(request)
        ):
            continue

        try:
            stats.append({
                "label": model._meta.verbose_name_plural.title(),
                "count": model.objects.count(),
                "url": f"/admin/{model._meta.app_label}/{model._meta.model_name}/",
                "icon": resolve_icon(model._meta.model_name),
            })
        except Exception:
            pass

    # SORTING
    sort_mode = get_setting("STAT_SORT")

    if sort_mode == "count_desc":
        stats.sort(key=lambda x: x["count"], reverse=True)

    elif sort_mode == "alpha":

        stats.sort(key=lambda x: x["label"])

    else:
    # default: count ascending
        stats.sort(key=lambda x: x["count"])

    # LIMIT
    stats = stats[: get_setting("STATS_LIMIT")]

    return {"stats": stats}
