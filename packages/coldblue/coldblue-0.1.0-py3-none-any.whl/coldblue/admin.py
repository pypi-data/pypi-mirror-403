from django.contrib.admin import AdminSite
from django.conf import settings


class ColdblueAdminSite(AdminSite):
    

    def each_context(self, request):
        context = super().each_context(request)

        # Read sidebar config from settings
        context["coldblue_sidebar"] = getattr(
            settings,
            "COLDBLUE_SIDEBAR",
            {"ENABLE": False}
        )

        return context
# Instantiate once so Django loads it
coldblue_admin_site = ColdblueAdminSite(name="coldblue")
