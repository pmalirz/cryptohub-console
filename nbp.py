from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
import logging
import requests 
from transaction import ExchangeRate, Transaction
from decimal import Decimal

logger = logging.getLogger(__name__)

class NBPClient:
    """Client for accessing NBP (National Bank of Poland) exchange rates."""
    
    BASE_URL = "https://api.nbp.pl/api/exchangerates/rates/A/{currency}/{start_date}/{end_date}/?format=json"
    

    def get_exchange_rates(
        self, 
        currency: str, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict[datetime.date, ExchangeRate]:
        """
        Get exchange rates for a currency and date range.
        
        Args:
            currency: Currency code (e.g., 'EUR', 'USD')
            start_date: Start date for rates
            end_date: End date for rates
            
        Returns:
            Dictionary mapping dates to ExchangeRate objects
        """
        url = self.BASE_URL.format(
            currency=currency,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return {
                datetime.strptime(rate["effectiveDate"], "%Y-%m-%d").date(): 
                ExchangeRate(
                    rateDate=datetime.strptime(rate["effectiveDate"], "%Y-%m-%d").date(),
                    rate=Decimal(str(rate["mid"])),  # Changed from float to Decimal
                    base_currency=currency,
                    quote_currency="PLN"
                )
                for rate in data["rates"]
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch rates for {currency}: {e}")
            return {}
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid response format for {currency}: {e}")
            return {}

    def get_rates_for_transactions(self, transactions: List[Transaction]) -> Dict[str, Dict[datetime.date, ExchangeRate]]:
        """
        Gets exchange rates for all currencies in transactions within their date ranges.
        
        Args:
            transactions: List of transactions to get rates for
            
        Returns:
            Dictionary mapping currency to date-rate mappings:
            {
                'EUR': { date1: ExchangeRate1, date2: ExchangeRate2, ... },
                'USD': { date1: ExchangeRate1, date2: ExchangeRate2, ... },
                ...
            }
        """
        # Group transactions by quote currency and find date ranges
        currency_dates = defaultdict(list)
        for tx in transactions:
            if tx.quote_currency != "PLN":
                currency_dates[tx.quote_currency].append(tx.time.date())
        
        # Get rates for each currency's date range
        rates_by_currency: Dict[str, Dict[datetime.date, ExchangeRate]] = {}
        
        for currency, dates in currency_dates.items():
            min_date = min(dates) - timedelta(days=7)  # Add 7-day margin
            max_date = max(dates)
            
            logger.info(f"Getting {currency} rates from {min_date} to {max_date}")
            rates = self.get_exchange_rates(currency, min_date, max_date)
            
            if rates:
                rates_by_currency[currency] = rates
            else:
                logger.error(f"Failed to get rates for {currency}")
        
        return rates_by_currency