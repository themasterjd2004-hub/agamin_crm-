from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db import models
class Request(models.Model):
    """
    Model representing a commercial request or CRM entry.
    """
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Request")
        verbose_name_plural = _("Requests")

    def __str__(self):
        return self.title


class CompanyType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
