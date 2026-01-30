from django import template
from django.conf import settings
from django.contrib import admin
from django.apps import apps

register = template.Library()

APP_LABEL_MAP = {
    "auth": "Authentication",
    "admin": "Administration",
    "contenttypes": "Content Types",
    "sessions": "Sessions",
    "sites": "Sites",
}

@register.simple_tag(takes_context=True)
def coldblue_sidebar(context):
    request = context["request"]
    cfg = getattr(settings, "COLDBLUE_SIDEBAR", {})
    sections = []

    # Sidebar disabled
    if not cfg.get("ENABLE", False):
        return sections

    sections_cfg = cfg.get("SECTIONS")

    # =========================================
    # AUTO MODE: ENABLE=True but no SECTIONS
    # =========================================
    if not sections_cfg:
        auto = {}

        for model, model_admin in admin.site._registry.items():
            if not model_admin.has_view_permission(request):
                continue

            app_label = model._meta.app_label
            auto.setdefault(app_label, []).append({
                "label": model._meta.verbose_name_plural.title(),
                "url": f"/admin/{app_label}/{model._meta.model_name}/",
                "icon": "fa-database",
            })

        for app_label, items in auto.items():
            sections.append({
               "label": APP_LABEL_MAP.get(app_label, app_label.title()),

                "icon": "fa-layer-group",
                "items": items,
            })

        return sections

    # =========================================
    # CUSTOM MODE: User-defined SECTIONS
    # =========================================
    for section in sections_cfg:
        items = []
        section_icon = section.get("icon") or "fa-database"

        for model_path in section.get("models", []):
            try:
                app_label, model_name = model_path.split(".")
                model = apps.get_model(app_label, model_name)
                model_admin = admin.site._registry.get(model)

                if not model_admin:
                    continue
                if not model_admin.has_view_permission(request):
                    continue

                items.append({
                    "label": model._meta.verbose_name_plural.title(),
                    "url": f"/admin/{app_label}/{model._meta.model_name}/",
                    "icon": section_icon,
                })

            except Exception:
                continue

        if items:
            sections.append({
                "label": section.get("label", ""),
                "icon": section_icon,
                "items": items,
            })

    return sections
