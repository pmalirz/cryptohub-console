import logging
import pandas as pd
import json
from datetime import datetime, date
from transaction import Transaction, ExchangeRate, TransactionForTax
from typing import List

logger = logging.getLogger(__name__)

def save_trades(trades: List[TransactionForTax]):
    # Convert to DataFrame-friendly format
    df_records = []
    for tax_tx in trades:
        record = {
            'platform': tax_tx.transaction.platform,
            'trade_id': tax_tx.transaction.trade_id,
            'pair': str(tax_tx.transaction.pair),
            'base_currency': str(tax_tx.transaction.base_currency),
            'quote_currency': str(tax_tx.transaction.quote_currency),
            'price': str(tax_tx.transaction.price),
            'time': tax_tx.transaction.time.strftime('%Y-%m-%d %H:%M:%S'),
            'volume': str(tax_tx.transaction.vol),
            'cost': str(tax_tx.transaction.cost),
            'fee': str(tax_tx.transaction.fee),
            'type': str(tax_tx.transaction.type),
            'tax_rate': str(tax_tx.tax_exchange_rate.rate),
            'tax_rate_date': tax_tx.tax_exchange_rate.rateDate.strftime('%Y-%m-%d'),
        }
        df_records.append(record)
        
    with open("tax_transactions.json", "w") as f:
        json.dump(df_records, f, indent=4)    

    df = pd.DataFrame(df_records)
    df.to_csv("tax_transactions.csv", index=False)
    
    logger.info("Saved tax transactions to tax_transactions.json and tax_transactions.csv")
