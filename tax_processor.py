from datetime import datetime, timedelta
import logging
from transaction import Transaction, TransactionForTax, ExchangeRate

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
            
        tx_date = transaction.time.date()
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