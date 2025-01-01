from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from .transaction import Transaction, TransactionForTax, ExchangeRate

logger = logging.getLogger(__name__)

def create_tax_transactions(
    transactions: list[Transaction], 
    rates_by_currency: dict[str, dict[datetime.date, ExchangeRate]], 
    settlement_day: int
) -> list[TransactionForTax]:
    """
    Create TransactionForTax objects by matching transactions with appropriate exchange rates.
    Looks backward for exchange rates up to specified number of days.
    
    Args:
        transactions: List of transactions to process
        rates_by_currency: Dictionary of exchange rates by currency and date
        settlement_day: Number of days to look back (must be <= 0)
    
    Returns:
        List of TransactionForTax objects
    """
    if settlement_day > 0:
        raise ValueError("settlement_day must be zero or negative")
        
    tax_transactions = []
    
    for transaction in transactions:
        if transaction.quote_currency == "PLN":
            continue
            
        currency_rates = rates_by_currency.get(transaction.quote_currency)
        if not currency_rates:
            logger.warning(f"No rates found for currency: {transaction.quote_currency}")
            continue
            
        tx_date = transaction.timestamp.date()
        exchange_rate = None
        
        # Look for exchange rate starting from transaction date and going backward 
        days_back = 0
        search_limit = abs(settlement_day)
        while True:
            search_date = tx_date - timedelta(days=days_back)
            
            if search_date in currency_rates:
                days_back += 1
            else:
                days_back += 1
                search_limit += 1
                continue                            
            
            if days_back >= search_limit:
                exchange_rate = currency_rates[search_date]                
                break                       
                            
        if exchange_rate:
            tax_transaction = TransactionForTax(
                transaction=transaction,
                tax_exchange_rate=exchange_rate
            )
            tax_transactions.append(tax_transaction)
        else:
            logger.warning(
                f"No exchange rate found for {transaction.quote_currency} "
                f"within {abs(settlement_day)} days of {tx_date}"
            )
    
    return tax_transactions


@dataclass
class Pit38Data:
    """
    Data structure representing fields in Polish PIT-38 tax form for cryptocurrency trading.
    All monetary values are in PLN, rounded to 2 decimal places.
    """
    year: int  # Tax year
    field34_income: Decimal  # Total income from crypto sales
    field35_costs_current_year: Decimal  # Costs from current year
    field36_costs_previous_years: Decimal  # Unused costs from previous years
    field37_tax_base: Decimal = field(init=False)  # Taxable income (if positive)
    field38_loss: Decimal = field(init=False)  # Loss (if negative)
    field39_tax: Decimal = field(init=False)  # 19% tax on positive income

    def __post_init__(self):
        """Calculate fields 37, 38 and 39 based on income and costs."""
        # Round input fields to 2 decimal places
        self.field34_income = self.field34_income.quantize(Decimal('0.01'))
        self.field35_costs_current_year = self.field35_costs_current_year.quantize(Decimal('0.01'))
        self.field36_costs_previous_years = self.field36_costs_previous_years.quantize(Decimal('0.01'))

        total_costs = self.field35_costs_current_year + self.field36_costs_previous_years
        result = self.field34_income - total_costs

        if result > 0:
            self.field37_tax_base = result.quantize(Decimal('0.01'))
            self.field38_loss = Decimal('0.00')
            # Calculate 19% tax, round to 2 decimal places
            self.field39_tax = (result * Decimal('0.19')).quantize(Decimal('0.01'))
        else:
            self.field37_tax_base = Decimal('0.00')
            self.field38_loss = abs(result).quantize(Decimal('0.01'))
            self.field39_tax = Decimal('0.00')


def calculate_pit_38(
    tax_transactions: list[TransactionForTax], 
    for_year: int, 
    previous_year_cost_field36: Decimal
) -> Pit38Data:
    """
    Calculate PIT-38 fields for cryptocurrency trading.
    
    Args:
        tax_transactions: List of transactions with tax exchange rates
        for_year: Tax year to calculate
        previous_year_cost_field36: Unused costs from previous years (field 36)
        
    Returns:
        Pit38Data object with calculated fields
    """
    # Filter transactions for the given year
    year_transactions = [
        tx for tx in tax_transactions 
        if tx.transaction.timestamp.year == for_year
    ]
    
    # Calculate total income (field 34) - sum of all sales
    income = sum(
        tx.total_cost_tax_currency 
        for tx in year_transactions 
        if tx.transaction.trade_type.upper() == "SELL"
    )
    
    # Calculate current year costs (field 35) - sum of all purchases
    current_year_costs = sum(
        tx.total_cost_tax_currency
        for tx in year_transactions 
        if tx.transaction.trade_type.upper() == "BUY"
    )
    
    pit38 = Pit38Data(
        year=for_year,
        field34_income=Decimal(income),
        field35_costs_current_year=Decimal(current_year_costs),
        field36_costs_previous_years=Decimal(previous_year_cost_field36)
    )
    
    return pit38