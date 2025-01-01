from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Transaction:
    platform: str
    pair: str
    base_currency: str
    quote_currency: str
    price: Decimal  # Changed from float to Decimal
    time: datetime
    ordertxid: str
    aclass: str
    maker: bool
    trade_id: str
    vol: Decimal    # Should also be Decimal
    ordertype: str
    cost: Decimal   # Should also be Decimal
    fee: Decimal    # Should also be Decimal
    postxid: str
    misc: str
    leverage: Decimal  # Changed if needed for precise calculations
    margin: Decimal    # Changed if needed for precise calculations
    type: str
 
@dataclass
class Pair:
    pair_id: str
    base_currency: str 
    quote_currency: str
    
@dataclass
class ExchangeRate:
    rateDate: datetime.date
    rate: Decimal   # Should also be Decimal
    base_currency: str 
    quote_currency: str # for Poland is PLN (for CryptoTaxPL this should be always PLN)  
    
@dataclass
class TransactionForTax:
    transaction: Transaction
    tax_exchange_rate: ExchangeRate