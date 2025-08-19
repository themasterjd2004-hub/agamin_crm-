from abc import ABC
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional
from django.db.models import Aggregate, CharField, Case, DecimalField, Exists, F, Max, OuterRef, Subquery, Sum, When, Count
from django.db.models.functions import Trunc
from django.db.models.query import QuerySet
from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings

from common.utils.helpers import get_today
from crm.models import Currency, Rate


class GroupConcat(Aggregate, ABC):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)'

    def __init__(self, expression, distinct=False, ordering=None, separator=', ', **extra):
        super().__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            ordering=' ORDER BY %s' % ordering if ordering is not None else '',
            separator=' SEPARATOR "%s"' % separator,
            output_field=CharField(),
            **extra
        )


def get_marketing_currency(request: Optional[WSGIRequest] = None) -> Optional[Currency]:
    """Get the marketing currency based on request or default settings."""
    currency_code = getattr(settings, 'MARKETING_CURRENCY_CODE', None)
    if currency_code:
        try:
            return Currency.objects.get(code=currency_code)
        except Currency.DoesNotExist:
            pass
    return None


def get_state_currency(request: Optional[WSGIRequest] = None) -> Optional[Currency]:
    """Get the state currency based on request or default settings."""
    currency_code = getattr(settings, 'STATE_CURRENCY_CODE', None)
    if currency_code:
        try:
            return Currency.objects.get(code=currency_code)
        except Currency.DoesNotExist:
            pass
    return None


def get_currency_info(request: Optional[WSGIRequest] = None) -> Tuple[str, str, str]:
    """
    Get currency information for display and calculations.
    Returns tuple of (currency_code, rate_field_name, button_title)
    """
    marketing_currency = get_marketing_currency(request) if request else get_marketing_currency()
    state_currency = get_state_currency(request) if request else get_state_currency()

    if marketing_currency is None and state_currency is None:
        return "USD", "rate_to_state_currency", "Default Currency"

    button_title = ""
    if marketing_currency and state_currency:
        button_title = f"{marketing_currency.name} > {state_currency.name}"
    elif marketing_currency:
        button_title = f"{marketing_currency.name}"
    elif state_currency:
        button_title = f"{state_currency.name}"

    currency_code = marketing_currency.code if marketing_currency else state_currency.code
    rate_field_name = "rate_to_marketing_currency" if marketing_currency else "rate_to_state_currency"

    return currency_code, rate_field_name, button_title


def get_current_currency_amount(payment_queryset: QuerySet, rate_field_name: str) -> Tuple[QuerySet, Decimal]:
    """Calculate the total amount in the specified currency."""
    rate = Rate.objects.filter(
        currency=OuterRef('currency'),
        payment_date=OuterRef('payment_date')
    )
    payment_queryset = payment_queryset.annotate(
        value=get_amount_in_currency(rate, rate_field_name)
    )
    total_data = payment_queryset.aggregate(amount=Sum('value'))
    total_amount = total_data['amount']
    return payment_queryset, round(total_amount, 2) if total_amount else Decimal('0')


def get_values_over_time(queryset: QuerySet, field: str) -> tuple:
    """Get values aggregated over time (by month)."""
    values = queryset.annotate(
        period=Trunc(field, 'month')
    ).values('period').annotate(
        total=Count('id')
    ).order_by('period')
    return check_time_periods(values), get_maximum(values)


def get_income_over_time(payment_queryset: QuerySet, field: str,
                        rate_field_name: str, earliest_date=None) -> tuple:
    """Get income values aggregated over time (by month) in specified currency."""
    rate = Rate.objects.filter(
        currency=OuterRef('currency'),
        payment_date=OuterRef('payment_date')
    )
    values = payment_queryset.annotate(
        period=Trunc(field, 'month')
    ).values('period').annotate(
        total=Sum(
            get_amount_in_currency(rate, rate_field_name)
        )
    ).order_by('period')
    return check_time_periods(values, earliest_date), get_maximum(values)


def get_amount_in_currency(rate: QuerySet, rate_field_name: str) -> Case:
    """Create a Case expression for calculating amount in specified currency."""
    return Case(
        When(Exists(rate),
             then=F('amount') * Subquery(rate.values(rate_field_name)[:1])),
        default=F('amount') * F(f'currency__{rate_field_name}'),
        output_field=DecimalField()
    )


def get_maximum(values: QuerySet) -> Decimal:
    """Get the maximum value from a values queryset."""
    value = values.aggregate(
        high=Max('total'),
    ).get('high', Decimal('0'))
    return value or Decimal('0')


def check_time_periods(queryset: QuerySet, earliest_date=None) -> list:
    """Ensure we have data for all periods in the last 12 months."""
    earliest_date = earliest_date or get_today()
    date = earliest_date.replace(day=1) + relativedelta(months=-11)
    return get_item_list(queryset, date)


def get_item_list(queryset: QuerySet, date) -> list:
    """Create a complete list of items for the last 12 months, filling in missing months."""
    item_list = list(queryset)
    if item_list and item_list[0]['period'] < date:
        item_list.pop(0)
    for i in range(0, 12):
        item = next((item for item in item_list if item["period"] == date), None)
        if not item:
            item_list.insert(i, {'period': date, 'total': Decimal('0')})
        date = date + relativedelta(months=1)
    return item_list
