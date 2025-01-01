from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

@dataclass
class Transaction:
    platform: str            # e.g. "Kraken", "Binance"
    trade_id: str            # Unique trade identifier
    trading_pair: str        # Unified trading pair (e.g. "BTCEUR")
    base_currency: str       # e.g. "BTC"
    quote_currency: str      # e.g. "EUR"
    price: Decimal           # Price per unit
    timestamp: datetime      # Execution date & time
    volume: Decimal          # Quantity traded
    total_cost: Decimal      # Total cost of the trade
    fee: Decimal             # Fee paid
    trade_type: str          # "BUY" or "SELL"

@dataclass
class Pair:
    symbol: str              # Trading pair symbol, e.g. "BTCEUR"
    base_currency: str       # Base currency (e.g. "BTC")
    quote_currency: str      # Quote currency (e.g. "EUR")

@dataclass
class ExchangeRate:
    rate_date: datetime.date # Effective date of the rate
    rate: Decimal            # Exchange rate (to PLN)
    base_currency: str       # Currency for which rate applies
    quote_currency: str      # Always "PLN" for tax conversion

@dataclass
class TransactionForTax:
    transaction: Transaction
    tax_exchange_rate: ExchangeRate
    total_cost_tax_currency: Decimal = field(init=False)

    def __post_init__(self):
        # If BUY add fee, if SELL subtract fee
        if self.transaction.trade_type.upper() == "BUY":
            self.total_cost_tax_currency = (self.transaction.total_cost + self.transaction.fee) * self.tax_exchange_rate.rate
        else:
            self.total_cost_tax_currency = (self.transaction.total_cost - self.transaction.fee) * self.tax_exchange_rate.rate