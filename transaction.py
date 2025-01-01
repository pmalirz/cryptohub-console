from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    platform: str
    pair: str
    base_currency: str
    quote_currency: str
    price: float
    time: datetime
    ordertxid: str
    aclass: str
    maker: bool
    trade_id: str
    vol: float
    ordertype: str
    cost: float
    fee: float
    postxid: str
    misc: str
    leverage: float
    margin: float
    type: str
 
@dataclass
class Pair:
    pair_id: str
    base_currency: str 
    quote_currency: str
    
@dataclass
class ExchangeRate:
    rateDate: datetime.date # date of the exchange rate (might be the same date or earlier as per logic T minus 0,1,2,3,...n)
    rate: float    
    base_currency: str 
    quote_currency: str # for Poland is PLN (for CryptoTaxPL this should be always PLN)  
    
@dataclass
class TransactionForTax:
    transaction: Transaction
    tax_exchange_rate: ExchangeRate  