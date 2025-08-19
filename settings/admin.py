from django.contrib import admin
from django.http import HttpResponseRedirect

from crm.site.crmadminsite import crm_site
from settings.models import BannedCompanyName
from settings.models import MassmailSettings
from settings.models import PublicEmailDomain
from settings.models import Reminders
from settings.models import StopPhrase


class BannedCompanyNameAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class MassmailSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "emails_per_day",
                    "use_business_time",
                    "business_time_start",
                    "business_time_end",
                    "unsubscribe_url",
                )
            },
        ),
    )

    # -- ModelAdmin methods -- #
    def changelist_view(self, request, extra_context=None):
        # Redirect to first object change page if exists
        qs = MassmailSettings.objects.all()
        if qs.exists():
            return HttpResponseRedirect(f"{request.path}{qs.first().id}/change/")
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request):
        return True  # Enable Add button

    def has_delete_permission(self, request, obj=None):
        return True  # Allow Delete if desired


class PublicEmailDomainAdmin(admin.ModelAdmin):
    list_display = ('domain',)
    search_fields = ('domain',)


class RemindersAdmin(admin.ModelAdmin):

    def changelist_view(self, request, extra_context=None):
        # Redirect to first object change page if exists
        qs = Reminders.objects.all()
        if qs.exists():
            return HttpResponseRedirect(f"{request.path}{qs.first().id}/change/")
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request):
        return True  # Enable Add button

    def has_delete_permission(self, request, obj=None):
        return True  # Allow Delete if desired


class StopPhraseAdmin(admin.ModelAdmin):
    actions = ['delete_selected']
    list_display = ('phrase', 'last_occurrence_date')
    search_fields = ('phrase',)


# Register models to crm_site
crm_site.register(BannedCompanyName, BannedCompanyNameAdmin)
crm_site.register(MassmailSettings, MassmailSettingsAdmin)
crm_site.register(PublicEmailDomain, PublicEmailDomainAdmin)
crm_site.register(Reminders, RemindersAdmin)
crm_site.register(StopPhrase, StopPhraseAdmin)

# Register models to default admin
admin.site.register(BannedCompanyName, BannedCompanyNameAdmin)
admin.site.register(MassmailSettings, MassmailSettingsAdmin)
admin.site.register(PublicEmailDomain, PublicEmailDomainAdmin)
admin.site.register(Reminders, RemindersAdmin)
admin.site.register(StopPhrase, StopPhraseAdmin)
