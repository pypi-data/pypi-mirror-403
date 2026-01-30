from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib import admin


class ColdblueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "coldblue"

    def ready(self):
        # =============================
        # Branding
        # =============================
        cfg = getattr(settings, "COLDBLUE_SETTINGS", {})

        site_title = cfg["SITE_TITLE"] if "SITE_TITLE" in cfg else "ADMIN LOGIN"
        site_header = cfg["SITE_HEADER"] if "SITE_HEADER" in cfg else "ADMIN PANEL"
        index_title = cfg["INDEX_TITLE"] if "INDEX_TITLE" in cfg else "ADMIN DASHBOARD"

        admin.site.site_title = site_title.upper()
        admin.site.site_header = site_header.upper()
        admin.site.index_title = index_title.upper()

        # =============================
        # Sidebar injection (SAFE)
        # =============================
        if hasattr(admin.site, "_coldblue_sidebar_patched"):
            return

        original_each_context = admin.site.each_context

        def each_context_with_sidebar(request):
            context = original_each_context(request)

            sidebar_cfg = getattr(settings, "COLDBLUE_SIDEBAR", {})

            # Sidebar disabled → clean exit
            if not sidebar_cfg.get("ENABLE", False):
                context["coldblue_sidebar"] = {
                    "ENABLE": False,
                    "SECTIONS": [],
                }
                return context

            sections = []

            for section in sidebar_cfg.get("SECTIONS", []):
                models = []
                section_icon = section.get("icon", "fa-database")

                for model_path in section.get("models", []):
                    try:
                        app_label, model_name = model_path.split(".")
                        model = apps.get_model(app_label, model_name)
                        model_admin = admin.site._registry.get(model)

                        if not model_admin:
                            continue

                        if not model_admin.has_view_permission(request):
                            continue

                        models.append({
                            "label": model._meta.verbose_name_plural.title(),
                            "url": f"/admin/{app_label}/{model._meta.model_name}/",
                            "icon": section_icon,
                        })

                    except Exception:
                        continue

                if models:
                    sections.append({
                        "label": section.get("label", ""),
                        "icon": section_icon,
                        "models": models,
                    })

            context["coldblue_sidebar"] = {
                "ENABLE": bool(sections),
                "SECTIONS": sections,
            }

            return context

        admin.site.each_context = each_context_with_sidebar
        admin.site._coldblue_sidebar_patched = True
