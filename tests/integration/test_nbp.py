import pytest
from datetime import datetime, timedelta, date
from pathlib import Path
from cryptohub.transaction import Transaction
from tests.test_helpers import load_sample_transactions
from cryptohub.nbp import NBPClient

@pytest.fixture
def nbp_client():
    return NBPClient()

@pytest.fixture
def sample_transactions():
    csv_path = Path(__file__).parent / 'sample_transactions.csv'
    return load_sample_transactions(str(csv_path))

def test_get_exchange_rates_date_range(nbp_client):
    """Test fetching exchange rates for different date ranges."""
    # Arrange
    currency = "EUR"
    end_date = datetime.now().date() 
    start_dates = [
        end_date - timedelta(days=7),
        end_date - timedelta(days=30)
    ]

    for start_date in start_dates:
        # Act
        rates = nbp_client.get_exchange_rates(currency, start_date, end_date)
        
        # Assert
        assert rates, f"Should return rates for {start_date} to {end_date}"
        assert all(start_date <= d <= end_date for d in rates.keys())
        assert all(isinstance(r.rate, float) and r.rate > 0 for r in rates.values())

def test_get_exchange_rates_multiple_currencies(nbp_client):
    """Test fetching rates for multiple currencies simultaneously."""
    # Arrange
    currencies = ["EUR", "USD", "GBP", "CHF"]
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=5)

    # Act
    results = {}
    for currency in currencies:
        rates = nbp_client.get_exchange_rates(currency, start_date, end_date)
        results[currency] = rates

    # Assert
    assert all(rates for rates in results.values()), "Should have rates for all currencies"
    assert all(
        rate.quote_currency == "PLN" 
        for rates in results.values() 
        for rate in rates.values()
    )

def test_get_rates_for_transactions_weekend_handling(nbp_client, sample_transactions):
    """Test handling of weekend dates when no rates are available."""
    # Filter transactions that occurred on weekends
    weekend_transactions = [
        tx for tx in sample_transactions 
        if tx.time.date().weekday() >= 5  # Saturday = 5, Sunday = 6
    ]
    
    if weekend_transactions:
        # Act
        rates = nbp_client.get_rates_for_transactions(weekend_transactions)
        
        # Assert
        assert rates, "Should return rates even for weekend transactions"
        for currency_rates in rates.values():
            assert currency_rates, "Should have rates for each currency"

def test_get_rates_for_transactions_with_gaps(nbp_client):
    """Test handling transactions with date gaps between them."""
    # Arrange
    current_date = datetime.now()
    transactions = [
        Transaction(
            pair="BTCEUR",
            base_currency="BTC",
            quote_currency="EUR",
            price=30000.0,
            time=current_date - timedelta(days=30),
            ordertxid="123",
            aclass="currency",
            maker=True,
            trade_id="1",
            vol=1.0,
            ordertype="limit",
            cost=30000.0,
            fee=10.0,
            postxid="456",
            misc="",
            leverage=0.0,
            margin=0.0,
            type="buy"
        ),
        Transaction(
            pair="BTCEUR",
            base_currency="BTC",
            quote_currency="EUR",
            price=35000.0,
            time=current_date,
            ordertxid="124",
            aclass="currency",
            maker=True,
            trade_id="2",
            vol=1.0,
            ordertype="limit",
            cost=35000.0,
            fee=10.0,
            postxid="457",
            misc="",
            leverage=0.0,
            margin=0.0,
            type="sell"
        )
    ]

    # Act
    rates = nbp_client.get_rates_for_transactions(transactions)

    # Assert
    assert "EUR" in rates
    assert len(rates["EUR"]) >= 2  # Should have at least rates for both transaction dates
    dates = sorted(rates["EUR"].keys())
    assert (dates[-1] - dates[0]).days >= 30  # Should span at least 30 days