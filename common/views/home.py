from django.conf import settings
from django.shortcuts import render

def home(request):
    apps = [
        {"name": "crm", "prefix": "crm", "models": ["Contact", "Lead", "Opportunity"]},
        {"name": "massmail", "prefix": "massmail", "models": ["Message", "Recipient"]},
        {"name": "tasks", "prefix": "tasks", "models": ["Task", "Subtask"]},
    ]
    context = {
        "site_title": "CRM Dashboard",
        "apps": apps,
        "admin_prefix": settings.SECRET_ADMIN_PREFIX.strip("/") + "/",
    }
    return render(request, "home.html", context)
