import requests
from requests.exceptions import JSONDecodeError
from typing import Union, Any, Tuple, Optional
from datetime import date
from django.utils.formats import date_format
from dataclasses import dataclass


@dataclass
class CurrencyInfo:
    code: str
    name: str
    rate: float


STATE_CURRENCY_CODE = 'UAH'
STATE_CURRENCY_NAME = 'Ukrainian Hryvnia'
DEFAULT_CURRENCY_CODE = 'USD'
DEFAULT_CURRENCY_NAME = 'US Dollar'


class BankGovUaBackend(BaseBackend):
    """Bank.gov.ua API backend for currency exchange rates"""

    CURRENCY_NAMES = {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'UAH': 'Ukrainian Hryvnia',
        # Add more currencies as needed
    }

    @classmethod
    def get_state_currency(cls) -> CurrencyInfo:
        return CurrencyInfo(
            code=STATE_CURRENCY_CODE,
            name=STATE_CURRENCY_NAME,
            rate=1.0  # State currency rate to itself is always 1
        )

    def __init__(
            self,
            currency: str = DEFAULT_CURRENCY_CODE,
            marketing_currency: str = DEFAULT_CURRENCY_CODE,
            rate_date: Optional[date] = None
    ):
        self.url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew"
        self.date_format = "Ymd"
        self.error = ''
        self.state_currency = self.get_state_currency()
        self.currency = currency
        self.marketing_currency = marketing_currency
        self.rate_date = rate_date if rate_date else date.today()
        self.data = self.get_data(marketing_currency)
        self.marketing_currency_rate = self.get_marketing_currency_rate()

    def get_currency_name(self, currency_code: str) -> str:
        """Get currency name from code with fallback to code"""
        return self.CURRENCY_NAMES.get(currency_code, currency_code)

    def get_data(self, currency: str = DEFAULT_CURRENCY_CODE) -> list:
        date_str = date_format(self.rate_date, format=self.date_format, use_l10n=False)
        params = {'date': date_str, 'valcode': currency, 'json': ''}
        try:
            response = requests.get(self.url, params=params)
            response.raise_for_status()
            return response.json()
        except JSONDecodeError:
            self.error = f"Failed to decode JSON response from API. Status: {response.status_code}. Response text: {response.text[:100]}"
            return []
        except requests.exceptions.RequestException as e:
            self.error = f"API request failed: {e}"
            return []

    def extract_rate_from_data(self, data: list, currency_code: str) -> float:
        """Extracts rate from API data list, handles errors, returns 1 on failure."""
        if self.error:
            return 1.0

        try:
            return float(data[0]['rate'])
        except (IndexError, KeyError, TypeError, ValueError) as e:
            self.error = f"Error processing API data for {currency_code}: {e}. Data received: {data}"
            return 1.0

    def get_marketing_currency_rate(self) -> float:
        return self.extract_rate_from_data(self.data, self.marketing_currency)

    def get_rate_to_state_currency(self, currency: str = DEFAULT_CURRENCY_CODE) -> CurrencyInfo:
        if currency == STATE_CURRENCY_CODE:
            return self.state_currency

        if self.error:
            return CurrencyInfo(
                code=currency,
                name=self.get_currency_name(currency),
                rate=1.0
            )

        currency_data = self.get_data(currency)
        rate = self.extract_rate_from_data(currency_data, currency)

        return CurrencyInfo(
            code=currency,
            name=self.get_currency_name(currency),
            rate=rate
        )

    def get_currency_info(self) -> Tuple[str, str, str]:
        """Returns (currency_code, rate_field_name, button_title)"""
        marketing = self.get_rate_to_state_currency(self.marketing_currency)
        state = self.state_currency

        button_title = f"{marketing.name} > {state.name}"

        return (
            marketing.code,
            "marketing_rate",
            button_title
        )