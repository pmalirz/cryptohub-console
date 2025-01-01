import logging
from typing import List
from datetime import datetime

import pandas as pd
from .config import Configuration
from .kraken import KrakenAPI
from .transaction import Transaction

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


def _create_dataframe(trades: list[Transaction]) -> pd.DataFrame:
    """Create a DataFrame from trade transactions."""
    df_records = []
    for trade in trades:
        record = {
            'Platform': trade.platform,
            'Trade ID': str(trade.trade_id),
            'Trading Pair': str(trade.trading_pair),
            'Base Currency': str(trade.base_currency),
            'Quote Currency': str(trade.quote_currency),
            'Price': float(trade.price),
            'Date & Time': trade.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Volume': float(trade.volume),
            'Total Cost': float(trade.total_cost),
            'Fee': float(trade.fee),
            'Type': str(trade.trade_type).upper(),
        }
        df_records.append(record)
    
    df = pd.DataFrame(df_records)
    
    # Set numeric columns type explicitly
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])
    
    return df


def save_trades_to_excel(trades: List[Transaction], filename: str = "trades.xlsx"):
    """
    Save trades to Excel with color formatting.
    Appends ISO date & time to the filename.
    """
    # Append ISO date and time (using underscores instead of colons) to the filename.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base, ext = filename.rsplit(".", 1)
    filename = f"{base}_{timestamp}.{ext}"

    df = _create_dataframe(trades)
    
    # Create Excel writer
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Trades', index=False)
    
    # Get workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Trades']
    
    # Define formats with Polish locale (comma as decimal separator)
    buy_format = workbook.add_format({'bg_color': '#C6EFCE'})  # Light green
    sell_format = workbook.add_format({'bg_color': '#FFC7CE'})  # Light red
    
    # Corrected number format: thousand separator (,) and 12 decimal places
    number_format = workbook.add_format({'num_format': '#,##0.000000000000'})  # US-style: 92,447,016.604180000000
        
    # Set numeric format for specific columns
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee']
    for col_name in numeric_columns:
        col_idx = df.columns.get_loc(col_name)
        worksheet.set_column(col_idx, col_idx, None, number_format)
    
    # Apply conditional formatting based on trade type
    type_col = df.columns.get_loc('Type') + 1  # Excel 1-based index
    worksheet.conditional_format(1, 0, len(df), len(df.columns)-1, {
        'type': 'formula',
        'criteria': f'=${chr(64+type_col)}2="BUY"',
        'format': buy_format
    })
    worksheet.conditional_format(1, 0, len(df), len(df.columns)-1, {
        'type': 'formula',
        'criteria': f'=${chr(64+type_col)}2="SELL"',
        'format': sell_format
    })
    
    # Auto-adjust columns width
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = max(series.astype(str).map(len).max(), len(str(series.name))) + 1
        worksheet.set_column(idx, idx, max_len)
    
    writer.close()
    
    logger.info(f"Saved trades to {filename}. You can open the file to make your own analysis and calculations.")
    
    # Use Rich Panel to notify the user with a friendly message
    console.print(f"💾 Saved trades to [blue]{filename}[/blue].")


def download_and_save_trades(config: Configuration):
    console.rule("[bold blue]Downloading Trades[/bold blue]")
    
    trades = []
    # Download trades from Kraken accounts.
    for account_id, account in config.kraken_accounts.items():
        # Pass filter_quote_assets from configuration.
        kraken = KrakenAPI(account.api_key, account.api_secret, account.name)
        account_trades = kraken.download_all_trades()
        trades.extend(account_trades)
        logger.info(f"Trades downloaded successfully for Kraken account: {account.name if account.name else 'Unnamed Account ' + account_id}")

    # Download trades from Binance accounts.
    from .binance import BinanceAPI  # Import BinanceAPI here.
    for account_id, account in config.binance_accounts.items():
        binance = BinanceAPI(account.api_key, account.api_secret, account.name, pair_pattern=account.pair_pattern)
        account_trades = binance.download_all_trades()
        trades.extend(account_trades)
        logger.info(f"Trades downloaded successfully for Binance account: {account.name if account.name else 'Unnamed Account ' + account_id}")

    # Save trades model to file.
    save_trades_to_excel(trades)
    
    return trades
