import threading
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, OuterRef, Subquery, Sum, Exists, F
from django.http import HttpResponseRedirect
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, gettext
from django.urls import reverse

from chat.models import ChatMessage
from common.admin import FileInline
from common.models import Department
from common.utils.helpers import (
    add_chat_context, set_toggle_tooltip, get_now, LEADERS,
    get_today, popup_window
)
from common.utils.remind_me import remind_me
from crm.forms.admin_forms import DealForm
from crm.models import (
    ClosingReason, CrmEmail, Deal, Output, Payment, Stage
)
from crm.site.crmmodeladmin import CrmModelAdmin
from crm.site.outputinline import OutputInline
from crm.site.paymentadmin import set_currency_initial
from crm.site.paymentinline import PaymentInline
from crm.utils.admfilters import (
    ByChangedByChiefs, ByOwnerFilter, ByProductFilter,
    ByPartnerFilter, ImportantFilter, IsActiveFilter,
    ScrollRelatedOnlyFieldListFilter
)
from crm.utils.clarify_permission import clarify_permission
from crm.utils.helpers import get_counterparty_header
from tasks.models import Memo

# Constants for icons and tooltips
closing_date_str = _("Closing date")
closing_date_safe_icon = mark_safe(
    f'<i class="material-icons" title="{closing_date_str}" '
    f'style="color: var(--body-quiet-color)">event_busy</i>'
)
icon_str = '<i class="material-icons" style="color: var(--body-quiet-color)">{}</i>'
contact_tip = _("View Contact in new tab")
company_tip = _("View Company in new tab")
company_safe_icon = mark_safe(icon_str.format('domain'))
deal_counter_icon = '<span title="{}">({})</span>'
deal_counter_title = _("Deal counter")
lead_tip = _("View Lead in new tab")
unanswered_email_str = _('Unanswered email')
mail_outline_small_icon = mark_safe(
    f'<i class="material-icons" title="{unanswered_email_str}" '
    f'style="font-size:small;color: var(--body-quiet-color)">mail_outline</i>'
)
mail_outline_safe_icon = mark_safe(icon_str.format('mail_outline'))
unread_chat_message_str = _('Unread chat message')
message_icon = mark_safe(
    f'<i class="material-icons" title="{unread_chat_message_str}" '
    f'style="font-size:small;color: var(--error-fg)">message</i>'
)
payment_received_str = _('Payment received')
payment_received_icon = mark_safe(
    f'<i class="material-icons" title="{payment_received_str}" '
    f'style="font-size:small;color:green">payments</i>'
)
specify_shipment_str = _('Specify the date of shipment')
local_shipping_icon = mark_safe(
    f'<i class="material-icons" title="{specify_shipment_str}" '
    f'style="font-size:small;color: var(--body-quiet-color)">local_shipping</i>'
)
specify_products_str = _('Specify products')
add_shopping_cart_icon = mark_safe(
    f'<i class="material-icons" title="{specify_products_str}" '
    f'style="font-size:small;color: var(--error-fg)">add_shopping_cart</i>'
)
expired_shipment_date_str = _('Expired shipment date')
expired_local_shipping_icon = mark_safe(
    f'<i class="material-icons" title="{expired_shipment_date_str}" '
    f'style="font-size:small;color: var(--error-fg)">local_shipping</i>'
)
perm_phone_msg_safe_icon = mark_safe(icon_str.format('perm_phone_msg'))
person_outline_safe_icon = mark_safe(icon_str.format('person_outline'))
textarea_tag = '<textarea name="description" cols="80" rows="5" class="vLargeTextField">{}</textarea>'
subject_icon = '<i title="{}" class="material-icons" style="color: var(--body-quiet-color)">subject</i>'
relevant_deal_str = _('Relevant deal')

_thread_local = threading.local()


class DealAdmin(CrmModelAdmin):
    actions = ['export_selected']
    empty_value_display = ''
    form = DealForm
    inlines = [OutputInline, PaymentInline, FileInline]
    list_filter = (
        ImportantFilter,
        IsActiveFilter,
        ByOwnerFilter,
        ByProductFilter,
        ByPartnerFilter,
        ByChangedByChiefs,
        'relevant',
        'creation_date',
        ('stage', ScrollRelatedOnlyFieldListFilter),
        ('closing_reason', ScrollRelatedOnlyFieldListFilter),
        ('company__industry', ScrollRelatedOnlyFieldListFilter),
    )
    list_per_page = 50
    raw_id_fields = (
        'lead',
        'contact',
        'company',
        'partner_contact',
        'request'
    )
    search_fields = [
        'name', 'next_step', 'description',
        'ticket', 'contact__first_name',
        'contact__last_name', 'contact__email',
        'contact__address', 'contact__description',
        'company__full_name', 'company__website',
        'company__city_name', 'company__country__name',
        'company__address', 'company__email',
        'company__description',
        'partner_contact__company__full_name',
        'lead__first_name', 'lead__last_name', 'lead__address',
        'lead__description', 'lead__company_name', 'lead__website',
        'lead__company_address',
        'lead__company_email',
    ]

    def _create_formsets(self, request, obj, change):
        formsets, inline_instances = super()._create_formsets(request, obj, change)

        if obj.pk:  # Only for saved instances
            try:
                last_payment = Payment.objects.filter(deal=obj).last()
                if last_payment:
                    payment_formset = formsets[1].empty_form.base_fields
                    payment_formset['amount'].initial = last_payment.amount
                    payment_formset['contract_number'].initial = last_payment.contract_number
                    payment_formset['invoice_number'].initial = last_payment.invoice_number
                    payment_formset['order_number'].initial = last_payment.order_number
                    if settings.MARK_PAYMENTS_THROUGH_REP:
                        payment_formset['through_representation'].initial = last_payment.through_representation
            except Exception as e:
                messages.warning(request, _("Could not load payment details: {}").format(str(e)))

        return formsets, inline_instances

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            obj = Deal.objects.get(id=object_id)
            extra_context.update({
                'emails': self.get_latest_emails('deal_id', object_id),
                'deal_num': Deal.objects.filter(company_id=obj.company_id).count(),
                'memo_num': Memo.objects.filter(deal_id=object_id).count()
            })

            content_type = ContentType.objects.get_for_model(Deal)
            add_chat_context(request, extra_context, object_id, content_type)
            self.add_remainder_context(request, extra_context, object_id, content_type)

            if settings.USE_I18N:
                for inline in self.inlines:
                    inline.verbose_name_plural = mark_safe(
                        f'{inline.icon} {inline.model._meta.verbose_name_plural}'
                    )
        except Deal.DoesNotExist:
            messages.error(request, _("Deal with ID '{}' does not exist").format(object_id))
            return HttpResponseRedirect(reverse("site:crm_deal_changelist"))

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        set_toggle_tooltip("deal_step_date_sorting", request, extra_context)

        next_url = request.get_full_path()
        extra_context.update({
            'toggle_sorting_url': f"{reverse('toggle_default_sorting')}?model=Deal&next_url={next_url}",
            'request_add_url': reverse("site:crm_request_add"),
            'has_add_request_permission': request.user.has_perm('crm.add_request')
        })

        func = getattr(self.__class__, 'dynamic_name')
        title = gettext(self.model._meta.get_field("name").help_text._args[0])
        func.short_description = mark_safe(subject_icon.format(title))

        _thread_local.department_id = {}
        return super().changelist_view(request, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "stage":
            kwargs["empty_label"] = None
        if db_field.name == 'currency':
            set_currency_initial(request, kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)

        newest_email = CrmEmail.objects.filter(
            deal=OuterRef('pk'),
            trash=False
        ).order_by('-creation_date')

        unread_chat = ChatMessage.objects.filter(
            content_type=ContentType.objects.get_for_model(Deal),
            object_id=OuterRef('pk'),
            recipients=request.user
        ).values('id')

        received_payments = Payment.objects.filter(
            deal=OuterRef('pk'),
            status=Payment.RECEIVED,
        ).values('id')

        product_exists = Output.objects.filter(deal=OuterRef('pk')).values('id')

        annotation_kwargs = {
            'is_unanswered_email': Subquery(newest_email.values('incoming')[:1]),
            'is_unanswered_inquiry': Subquery(newest_email.values('inquiry')[:1]),
            'is_unread_chat': Exists(unread_chat),
            'is_received_payment': Exists(received_payments),
            'is_no_product': ~Exists(product_exists),
        }

        if settings.SHIPMENT_DATE_CHECK:
            today = get_today()
            expired_shipment = Output.objects.filter(
                deal=OuterRef('pk'),
                shipping_date__lt=today
            ).values('id')

            empty_date = Output.objects.filter(
                deal=OuterRef('pk'),
                shipping_date__isnull=True
            ).values('id')

            annotation_kwargs.update({
                'is_empty_shipping_date': Exists(empty_date),
                'is_expired_shipment_date': Exists(expired_shipment),
                'is_goods_shipped': F('stage__goods_shipped')
            })

        cl.result_list = cl.result_list.annotate(**annotation_kwargs)
        return cl

    def get_fieldsets(self, request, obj=None):
        inquiry = None
        contact_fields = []

        if obj:
            if obj.request:
                inquiry = obj.request
                inquiry_url = reverse('site:crm_request_change', args=(obj.request.id,))
                title = _('View the Request')
                func = getattr(self.__class__, 'inquiry')
                func.short_description = mark_safe(
                    f'<ul class="object-tools" style="margin-left: -40px;margin-top: 0px;">'
                    f'<li><a title="{title}" href="{inquiry_url}" target="_blank">'
                    f'{_("Request")}'
                    f' </a></li></ul>'
                )

            person = obj.contact or obj.lead
            for attr in ('phone', 'other_phone', 'mobile'):
                if getattr(person, attr, None):
                    contact_fields.append('connections_to_' + attr)

        fields = ['name']
        if inquiry:
            fields.append(('inquiry', 'translation') if inquiry.translation else 'inquiry')

        fields.extend([
            ('relevant', 'important', 'created'),
            ('closing_reason', 'closed')
        ])

        return (
            (None, {'fields': fields}),
            (_('Contact info'), {
                'fields': (
                    'contact_person', 'create_email',
                    *contact_fields, 'deal_messengers',
                    'view_website_button', 'view_company',
                )
            }),
            (' ', {
                'fields': (
                    'stage',
                    ('amount', 'currency'),
                    ('paid', 'expected'),
                    'next_step', ('next_step_date', 'remind_me'),
                    'workflow_area', 'description',
                    'stages_dates',
                )
            }),
            (' ', {'fields': ('tag_list',)}),
            *self.get_tag_fieldsets(obj),
            (_('Relations'), {
                'classes': ('collapse',),
                'fields': (
                    'contact', 'company',
                    'lead', 'partner_contact',
                    'request'
                )
            }),
            (_('Additional information'), {
                'classes': ('collapse',),
                'fields': (
                    ('owner', 'co_owner'),
                    ('modified_by', 'update_date'),
                    'ticket'
                )
            }),
        )

    def get_list_display(self, request):
        list_display = [
            'dynamic_name', 'attachment', 'marks',
            'next_step_name', 'coloured_next_step_date',
            'stage', 'counterparty'
        ]

        if not any(('company' in request.GET, 'lead' in request.GET)):
            list_display.append('deal_counter')

        if not (request.user.is_manager and 'owner' not in request.GET):
            list_display.append('person')

        list_display.extend(['act', 'rel', 'created', 'id'])
        return list_display

    def get_ordering(self, request):
        if hasattr(request, 'session') and "deal_step_date_sorting" in request.session:
            return 'next_step_date',
        return '-id',

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            'creation_date', 'update_date',
            'created', 'inquiry', 'workflow',
            'ticket', 'modified_by', 'stages_dates',
            'closing_date', 'translation',
            'coloured_next_step_date', 'rel',
            'act', 'person', 'contact_person',
            'deal_messengers', 'view_website_button',
            'view_company', 'tag_list', 'dynamic_name',
            'counterparty', 'workflow_area', 'marks',
            'create_email', 'connections_to_phone',
            'connections_to_other_phone',
            'connections_to_mobile', 'closed',
            'paid', 'expected', 'attachment', 'deal_counter'
        ]

        if request.user.is_chief:
            readonly_fields.extend((
                'name', 'relevant', 'active',
                'closing_reason', 'stage',
                'amount', 'currency', 'description',
                'products', 'tags', 'contact',
                'request', 'lead', 'company',
                'partner_contact', 'owner'
            ))

        return readonly_fields

    def has_change_permission(self, request, obj=None):
        value = super().has_change_permission(request, obj)
        if not value or not obj:
            return value
        return clarify_permission(request, obj)

    def response_post_save_change(self, request, obj):
        if '_create_email_to_partner' in request.POST:
            url = reverse(
                'create_email', args=(obj.pk,)
            ) + '?object=deal&recipient=partner_contact'
            return HttpResponseRedirect(url)
        return super().response_post_save_change(request, obj)

    def save_model(self, request, obj, form, change):
        now = get_now()
        today = get_today()
        formatted_today = date_format(today, format="SHORT_DATE_FORMAT", use_l10n=True)

        # Set default stage if none exists
        if not obj.stage:
            obj.stage = Stage.objects.get(
                default=True,
                department=obj.department
            )

        # Handle next step changes
        if 'next_step' in form.changed_data:
            if request.user != obj.owner:
                next_step = obj.next_step + f' ({request.user.username})'
                next_step_len = len(next_step)
                if next_step_len > 250:
                    obj.next_step = truncatechars(obj.next_step, 250 - len(f' ({request.user.username})'))
                obj.next_step += f' ({request.user.username})'
            obj.add_to_workflow(obj.next_step)

        # Handle closing reason changes
        if 'closing_reason' in form.changed_data:
            obj.active = not bool(obj.closing_reason)
            if obj.closing_reason:
                obj.closing_date = today
                if obj.closing_reason.success_reason:
                    obj.stage = Stage.objects.get(
                        success_stage=True,
                        department=obj.department
                    )
                    obj.change_stage_data(formatted_today)
                    obj.win_closing_date = now
            else:
                obj.closing_date = None

        # Handle stage changes
        if 'stage' in form.changed_data:
            obj.change_stage_data(formatted_today)
            if obj.stage:
                success_stages = Stage.objects.filter(
                    Q(success_stage=True) | Q(conditional_success_stage=True),
                    department=obj.department
                )
                if obj.stage in success_stages:
                    obj.win_closing_date = now

        # Handle active/relevant status changes
        if 'active' in form.changed_data:
            if obj.active:
                obj.relevant = True
            else:
                obj.closing_date = today

        if 'relevant' in form.changed_data and not obj.relevant:
            obj.active = False
            obj.closing_date = today

        # Handle owner changes
        if 'owner' in form.changed_data and obj.lead:
            obj.lead.owner = obj.owner
            obj.lead.save()

        # Handle second default stage for existing deals
        if change and obj.stage and obj.stage == Stage.objects.get(
                default=True,
                department=obj.department
        ):
            second_default_stage = Stage.objects.filter(
                second_default=True,
                department=obj.department
            ).first()
            if second_default_stage:
                obj.stage = second_default_stage

        # Mark as not new if owned by current user
        if obj.is_new and obj.owner == request.user:
            obj.is_new = False

        self.set_owner(request, obj)
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        remind_me(request, form, change)

        # Delete unreceived payments if deal is closed unsuccessfully
        obj = form.instance
        if 'closing_reason' in form.changed_data and not obj.active:
            if not obj.closing_reason.success_reason:
                Payment.objects.filter(deal=obj).exclude(
                    status=Payment.RECEIVED,
                ).delete()

    # ----- Display Methods ----- #

    @admin.display(description=person_outline_safe_icon)
    def contact_person(self, obj):
        if not obj.contact and not obj.lead:
            return LEADERS

        if obj.contact:
            url = reverse('site:crm_contact_change', args=(obj.contact_id,))
            name = obj.contact.full_name
        else:
            url = reverse('site:crm_lead_change', args=(obj.lead_id,))
            name = obj.lead.full_name

        return mark_safe(
            f'{name} <ul class="object-tools" style="margin-left: 0px;margin-top: 0px;">'
            f'<li><a title="{contact_tip}" href="#" onClick="{popup_window(url)}">'
            f'<i class="material-icons" style="font-size: 17px;vertical-align: middle;">visibility</i> '
            f'<i class="material-icons" style="font-size: 17px;vertical-align: middle;">edit</i>'
            f'</a></li></ul>'
        )

    @admin.display(description=get_counterparty_header())
    def counterparty(self, obj):
        counterparty = obj.lead if obj.lead else obj.company
        if not counterparty:
            return LEADERS

        if hasattr(_thread_local, 'deal_changelist_url'):
            url = _thread_local.deal_changelist_url
        else:
            url = reverse("site:crm_deal_changelist")
            _thread_local.deal_changelist_url = url

        url += f"?{counterparty._meta.model_name}={counterparty.id}&active=all"
        name = counterparty.full_name

        if obj.department:
            if obj.department_id in _thread_local.department_id:
                works_globally = _thread_local.department_id[obj.department_id]
            else:
                works_globally = Department.objects.get(id=obj.department_id).works_globally
                _thread_local.department_id[obj.department_id] = works_globally

            if works_globally and hasattr(counterparty, 'country'):
                name += f", {counterparty.country}"

        return mark_safe(f'<a href="{url}">{name}</a>')

    @admin.display(description=mail_outline_safe_icon)
    def create_email(self, obj):
        if not obj.id:
            return LEADERS

        recipient = title = ''
        if getattr(obj.contact, 'email', None):
            recipient = obj.contact._meta.model_name
            title = _("Create Email to Contact")
        elif getattr(obj.lead, 'email', None):
            recipient = obj.lead._meta.model_name
            title = _("Create Email to Lead")

        if not recipient:
            return LEADERS

        url = reverse('create_email', args=(obj.id,)) + f"?object=deal&recipient={recipient}"
        return mark_safe(
            f'<ul class="object-tools" style="margin-left: 0px;margin-top: 0px;">'
            f'<li><a title="{title}" href="#" onClick="{popup_window(url)}"> '
            '<i class="material-icons" style="font-size: 17px;vertical-align: middle;">create</i> '
            '<i class="material-icons" style="font-size: 17px;vertical-align: middle;">drafts</i>'
            ' </a></li></ul>'
        )

    @staticmethod
    @admin.display(description='')
    def deal_counter(obj):
        if obj.company:
            counter = Deal.objects.filter(company=obj.company).count()
        elif obj.lead:
            counter = Deal.objects.filter(lead=obj.lead).count()
        else:
            return ''

        return mark_safe(deal_counter_icon.format(deal_counter_title, counter))

    @admin.display(description=perm_phone_msg_safe_icon)
    def deal_messengers(self, obj):
        instance = obj.contact if obj.contact else obj.lead
        if not instance:
            return ''
        return self.messengers(instance)

    @admin.display(ordering='name')
    def dynamic_name(self, obj):
        if obj.important:
            return mark_safe('<mark title="{title}">{name}</mark>'.format(
                title=gettext("Important deal"),
                name=obj.name)
            )
        return obj.name

    @staticmethod
    def inquiry(obj):
        if not obj.request:
            return ''
        text = obj.request.description
        return mark_safe(textarea_tag.format(text))

    @admin.display(description='')
    def marks(self, instance):
        icons = ''

        # Unanswered inquiry icon
        if getattr(instance, 'is_unanswered_inquiry', False):
            inquiry = CrmEmail.objects.filter(
                deal=instance,
                inquiry=True,
                trash=False
            ).order_by('-creation_date').annotate(
                subsequent=F('request__subsequent')
            ).values('creation_date', 'subsequent').first()

            if not inquiry['subsequent']:
                days = (timezone.now() - inquiry['creation_date']).days
                title = _('I have been waiting for an answer to my request for %d days') % days

                if days == 2:
                    icon = f'<i class="material-icons" title="{title}" style="font-size:small;color: var(--body-quiet-color)">sentiment_neutral</i>'
                elif days in (3, 4):
                    icon = f'<i class="material-icons" title="{title}" style="font-size:small;color: var(--body-quiet-color)">sentiment_dissatisfied</i>'
                elif days in (5, 6):
                    icon = f'<i class="material-icons" title="{title}" style="font-size:small;color: var(--body-quiet-color)">sentiment_very_dissatisfied</i>'
                elif days >= 7:
                    icon = f'<i class="material-icons" title="{title}" style="font-size:small;color: var(--error-fg)">mood_bad</i>'

                icons += icon
        elif getattr(instance, 'is_unanswered_email', False):
            icons += mail_outline_small_icon

        # Unread chat message icon
        if getattr(instance, 'is_unread_chat', False):
            icons += message_icon

        # Payment received icons
        if getattr(instance, 'is_received_payment', False):
            icons += payment_received_icon
            if getattr(instance, 'is_empty_shipping_date', False):
                icons += local_shipping_icon
            if instance.is_no_product:
                icons += add_shopping_cart_icon

        # Expired shipment icon
        if (getattr(instance, 'is_expired_shipment_date', False) and
                getattr(instance, 'is_active', True)):
            icons += expired_local_shipping_icon

        return mark_safe(icons)

    @admin.display(description=_('Expected'))
    def expected(self, obj):
        expected_amount = 0
        currency = obj.currency if obj.currency else ''
        if obj.amount:
            expected_amount = max(obj.amount - obj.paid_amount, 0)
        return f"{expected_amount} {currency}"

    @admin.display(description=_('Paid'))
    def paid(self, obj):
        obj.paid_amount = 0
        currency = obj.currency if obj.currency else ''
        if obj.amount:
            try:
                paid_amount = Payment.objects.filter(
                    deal=obj,
                    status=Payment.RECEIVED
                ).aggregate(amount=Sum('amount'))['amount'] or 0
                obj.paid_amount = paid_amount
            except Exception:
                obj.paid_amount = 0
        return f"{obj.paid_amount} {currency}"

    @admin.display(
        description=mark_safe(f'<div title="{relevant_deal_str}">{gettext("Rel")}</div>'),
        ordering='relevant',
        boolean=True
    )
    def rel(self, obj):
        return obj.relevant

    @admin.display(
        description=closing_date_safe_icon,
        ordering='closing_date'
    )
    def closed(self, obj):
        return obj.closing_date or LEADERS

    @admin.display(description=_('Translation'))
    def translation(self, obj):
        if not obj.request or not obj.request.translation:
            return ''
        text = obj.request.translation
        return mark_safe(
            f'<textarea name="description" cols="80" rows="5" '
            f'class="vLargeTextField">{text}</textarea>'
        )

    @admin.display(description=company_safe_icon)
    def view_company(self, obj):
        if obj.company:
            company = ', '.join(
                (obj.company.full_name, obj.company.country.name)
            )
            company_url = reverse(
                'site:crm_company_change', args=(obj.company_id,)
            )
            li = f'<li><a title="{company_tip}" href="#" onClick="{popup_window(company_url)}">' \
                 f'<i class="material-icons" style="font-size: 17px;vertical-align: middle;">visibility</i> ' \
                 f'<i class="material-icons" style="font-size: 17px;vertical-align: middle;">edit</i>' \
                 f'</a></li>'
            return mark_safe(
                f'{company} <ul class="object-tools" style="margin-left: 0px;margin-top: 0px;">{li}</ul>'
            )
        if obj.lead:
            return _("Contact is Lead (no company)")
        return LEADERS