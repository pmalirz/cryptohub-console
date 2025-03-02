import csv
from decimal import Decimal
from datetime import datetime
from cryptohub.transaction import Transaction


def load_sample_transactions(csv_path: str) -> list[Transaction]:
    transactions = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(Transaction(
                platform=row['platform'],
                trade_id=row['trade_id'],
                trading_pair=row['trading_pair'],
                base_currency=row['base_currency'],
                quote_currency=row['quote_currency'],
                price=Decimal(row['price']),
                timestamp=datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                volume=Decimal(row['volume']),
                total_cost=Decimal(row['total_cost']),
                fee=Decimal(row['fee']),
                trade_type=row['trade_type']
            ))
    return 
