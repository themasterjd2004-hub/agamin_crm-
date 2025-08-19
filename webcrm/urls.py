from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.shortcuts import redirect
from django.views.generic import DetailView, CreateView
from crm.models import Request  # Example model

from common.views.favicon import FaviconRedirect
from crm.views.contact_form import contact_form
from massmail.views.get_oauth2_tokens import get_refresh_token


# ---------------------------
# Root redirect to language-prefixed homepage
# ---------------------------
def root_redirect(request):
    return redirect(f'/{settings.SECRET_CRM_PREFIX}')  # e.g., /en/123/


# ---------------------------
# Top-level URL patterns
# ---------------------------
urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    path('favicon.ico', FaviconRedirect.as_view()),
    path('voip/', include('voip.urls')),
    path(
        'OAuth-2/authorize/',
        staff_member_required(get_refresh_token),
        name='get_refresh_token'
    ),
]

# ---------------------------
# Media files (development only)
# ---------------------------
urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

# ---------------------------
# Optional Rosetta URLs (if installed)
# ---------------------------
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('rosetta/', include('rosetta.urls'))
    ]

# ---------------------------
# Internationalized URL patterns
# ---------------------------
urlpatterns += i18n_patterns(
    # Frontend common URLs
    path(settings.SECRET_CRM_PREFIX, include('common.urls')),

    # CRM object operations
    path(
        f'{settings.SECRET_CRM_PREFIX}<int:pk>/',
        staff_member_required(DetailView.as_view(
            model=Request,
            template_name='crm/object_detail.html'
        )),
        name='object-detail'
    ),
    path(
        f'{settings.SECRET_CRM_PREFIX}add/',
        staff_member_required(CreateView.as_view(
            model=Request,
            template_name='crm/object_form.html',
            fields='__all__',
            success_url='/'
        )),
        name='object-add'
    ),

    # Include CRM, MassMail, and Tasks URLs
    path(settings.SECRET_CRM_PREFIX, include('crm.urls')),
    path(settings.SECRET_CRM_PREFIX, include('massmail.urls')),
    path(settings.SECRET_CRM_PREFIX, include('tasks.urls')),

    # Admin redirect (fix for 404 at /en/456-admin/)
    path(
        settings.SECRET_ADMIN_PREFIX,
        lambda request: redirect(f'/{request.LANGUAGE_CODE}/{settings.SECRET_ADMIN_PREFIX}/')
        if request.user.is_authenticated
        else redirect(f'/{request.LANGUAGE_CODE}/{settings.SECRET_ADMIN_PREFIX}/login/')
    ),

    # Admin URLs (kept after redirect so index/login works)
    path(f'{settings.SECRET_ADMIN_PREFIX}/', admin.site.urls),

    # Contact form
    path('contact-form/<uuid:uuid>/', contact_form, name='contact_form'),
)
