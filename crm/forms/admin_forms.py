import json
from email.utils import parseaddr
from django import forms
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.validators import EmailValidator
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from crm.models import ClosingReason
from crm.models import Company
from crm.models import Contact
from crm.models import CrmEmail
from crm.models import Currency
from crm.models import Deal
from crm.models import Lead
from crm.models import Request
from crm.models import Tag
from crm.utils.helpers import phone_number_check
from tasks.forms import clean_next_step_date

COUNTRY_WARNING = _("A country must be specified.")
marketing_exists_str = _('Marketing currency already exists.')
STATE_EXISTS_STR = _('State currency already exists.')
WRONG_CODE_WARNING = _("Enter a valid alphabetic code.")
cannot_be_both_str = _("The currency cannot be both state and marketing.")


class IoMail(forms.ModelForm):
    class Meta:
        model = CrmEmail
        fields = '__all__'
        widgets = {
            'to': forms.Textarea(attrs={'cols': 80, 'rows': 2}),
            'cc': forms.Textarea(attrs={'cols': 80, 'rows': 2}),
            'bcc': forms.Textarea(attrs={'cols': 80, 'rows': 2}),
            'subject': forms.Textarea(attrs={'cols': 80, 'rows': 2})
        }

    def _media(self):
        if not all((self.instance.incoming, self.instance.uid)):
            js = (
                '/static/common/js/vendor/nicEdit.js',
                '/static/common/js/vendor/textarea_content.js'
            )
            return forms.Media(js=js)
        return forms.Media()

    media = property(_media)

    def clean(self):
        cleaned_data = super().clean()
        if hasattr(settings, 'NOT_ALLOWED_EMAILS') and settings.NOT_ALLOWED_EMAILS:
            for field in ('to', 'cc'):
                field_value = cleaned_data.get(field)
                if field_value:
                    for adr in settings.NOT_ALLOWED_EMAILS:
                        if adr in field_value:
                            msg = _("Not allowed address")
                            err_msg = f'{msg}: "{adr}"'
                            self.add_error(field, err_msg)
        return cleaned_data


class BaseCallablesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        for field in self.fields.keys():
            self.fields[field].label_suffix = ":"

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get("city")
        country = cleaned_data.get("country")
        if city and country and city.country_id != country.id:
            msg = _("City does not match the country")
            self.add_error('city', msg)
            self.add_error('country', msg)
        return cleaned_data

    def clean_email(self):
        value = self.cleaned_data.get("email")
        if value:
            email_validator = EmailValidator()
            for email in value.split(","):
                email_validator(parseaddr(email.strip())[1])
        return value


class CompanyForm(BaseCallablesForm):
    class Meta:
        model = Company
        fields = '__all__'


class BaseContactForm(BaseCallablesForm):
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if first_name and last_name:
            q_params = Q()
            email = cleaned_data.get("email")
            phone = cleaned_data.get("phone")
            mobile = cleaned_data.get("mobile")
            other_phone = cleaned_data.get("other_phone")

            if email:
                q_params |= Q(email=email)
            if phone:
                q_params |= Q(phone=phone)
            if mobile:
                q_params |= Q(mobile=mobile)
            if other_phone:
                q_params |= Q(other_phone=other_phone)

            if q_params:
                model = self.Meta.model
                doubles = model.objects.all()
                if self.instance:
                    doubles = doubles.exclude(id=self.instance.id)

                double = doubles.filter(
                    q_params,
                    first_name=first_name,
                    last_name=last_name
                ).first()

                if double:
                    url = reverse(
                        f"site:crm_{model._meta.model_name}_change",
                        args=(double.id,)
                    )
                    msg = _("Such an object already exists")
                    link = f'<a href="{url}" target="_blank">{msg} - ID{double.id}</a>'
                    raise forms.ValidationError(mark_safe(link), code="invalid")
        return cleaned_data


class ContactForm(BaseContactForm):
    class Meta:
        model = Contact
        fields = '__all__'


class LeadForm(BaseContactForm):
    name = forms.CharField(required=True, label=_("Name"))

    class Meta:
        model = Lead
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if getattr(self, 'convert', None):
            contact = cleaned_data.get("contact")
            company = cleaned_data.get("company")

            if not contact and not company:
                is_missed_field = False
                fields = getattr(settings, 'CONVERT_REQUIRED_FIELDS', ['name', 'email', 'phone'])
                msg = _('Please fill in the field.')

                for field in fields:
                    if not cleaned_data.get(field):
                        self.add_error(field, forms.ValidationError(msg, code='invalid'))
                        is_missed_field = True

                if is_missed_field:
                    raise forms.ValidationError(
                        _('To convert, please fill in the fields below.'),
                        code='invalid'
                    )
        return cleaned_data


class DealForm(BaseCallablesForm):
    class Meta:
        model = Deal
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'cols': 75, 'rows': 2}),
            'next_step': forms.Textarea(attrs={'cols': 75, 'rows': 2}),
            'description': forms.Textarea(attrs={'cols': 75, 'rows': 5}),
        }

    class Media:
        css = {'all': ('/static/common/css/deal_module.css',)}

    def clean(self):
        cleaned_data = super().clean()
        closing_reason = cleaned_data.get("closing_reason")
        amount = cleaned_data.get("amount")

        if closing_reason and not amount:
            department = self.instance.department
            cr = ClosingReason.objects.filter(
                success_reason=True,
                department=department
            ).first()

            if cr and closing_reason == cr:
                raise forms.ValidationError({
                    NON_FIELD_ERRORS: _("Specify the deal amount"),
                    'amount': _("Specify the deal amount"),
                }, code='invalid')

        clean_next_step_date(self)
        return cleaned_data


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = '__all__'
        widgets = {
            'request_for': forms.Textarea(attrs={'cols': 80, 'rows': 2}),
            'remark': forms.Textarea(attrs={'cols': 80, 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company")
        contact = cleaned_data.get("contact")
        lead = cleaned_data.get("lead")

        if any((contact, lead)) and 'first_name' in self._errors:
            del self._errors['first_name']

        if contact and company and contact.company_id != company.id:
            msg = _("Contact does not match the company")
            self.add_error('contact', msg)
            self.add_error('company', msg)

        if contact and lead:
            msg = _("Select only Contact or only Lead")
            self.add_error('contact', msg)
            self.add_error('lead', msg)

        if company and lead:
            msg = _("Select only Company or only Lead")
            self.add_error('lead', msg)
            self.add_error('company', msg)

        if self.errors:
            raise forms.ValidationError(self.errors, code='invalid')
        return cleaned_data

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if getattr(self, "country_must_be_specified", False) and not country:
            raise forms.ValidationError(COUNTRY_WARNING, code='invalid')
        return country

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone_number_check(phone)
        return phone


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = '__all__'

    def check_currencies(self, field: str, message: str) -> None:
        value = self.cleaned_data[field]
        if value:
            currencies = Currency.objects.filter(**{field: True})
            if self.instance:
                currencies = currencies.exclude(id=self.instance.id)
            if currencies.exists():
                raise forms.ValidationError(message, code='invalid')

    def clean_is_marketing_currency(self):
        self.check_currencies('is_marketing_currency', marketing_exists_str)
        return self.cleaned_data['is_marketing_currency']

    def clean_is_state_currency(self):
        self.check_currencies('is_state_currency', STATE_EXISTS_STR)
        return self.cleaned_data['is_state_currency']

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            file_path = settings.BASE_DIR / 'crm' / 'forms' / 'iso_currency_codes.json'
            with open(file_path, 'r') as f:
                data = json.load(f)
                if name not in data:
                    raise forms.ValidationError(WRONG_CODE_WARNING, code='invalid')
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return name

    def clean(self):
        cleaned_data = super().clean()
        is_state = cleaned_data.get("is_state_currency")
        is_marketing = cleaned_data.get("is_marketing_currency")

        if is_state and is_marketing:
            self.add_error('is_state_currency', cannot_be_both_str)
            self.add_error('is_marketing_currency', cannot_be_both_str)
            raise forms.ValidationError(cannot_be_both_str, code='invalid')
        return cleaned_data


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('name', 'department')
        widgets = {'department': forms.HiddenInput()}

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        department = cleaned_data.get('department')

        if name and department:
            queryset = Tag.objects.filter(
                name__iexact=name,
                department=department
            )
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise forms.ValidationError(
                    _("Such a tag already exists."), code='invalid')
        return cleaned_data