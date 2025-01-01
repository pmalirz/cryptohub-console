import csv
from datetime import datetime
from cryptohub.transaction import Transaction

def load_sample_transactions(csv_path: str) -> list[Transaction]:
    transactions = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(Transaction(
                pair=row['pair'],
                base_currency=row['base_currency'],
                quote_currency=row['quote_currency'],
                price=float(row['price']),
                time=datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                ordertxid=row['ordertxid'],
                aclass=row['aclass'],
                maker=row['maker'].lower() == 'true',
                trade_id=row['trade_id'],
                vol=float(row['vol']),
                ordertype=row['ordertype'],
                cost=float(row['cost']),
                fee=float(row['fee']),
                postxid=row['postxid'],
                misc=row['misc'],
                leverage=float(row['leverage']),
                margin=float(row['margin']),
                type=row['type']
            ))
    return transactions