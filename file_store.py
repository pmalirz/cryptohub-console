import logging
import pandas as pd
from datetime import datetime, date
from transaction import Transaction, ExchangeRate, TransactionForTax
from typing import List
import locale
from decimal import Decimal

logger = logging.getLogger(__name__)

# Set Polish locale
locale.setlocale(locale.LC_NUMERIC, 'pl_PL.utf8')

def _create_dataframe(trades: List[TransactionForTax]) -> pd.DataFrame:
    """Create a DataFrame from tax transactions."""
    df_records = []
    for tax_tx in trades:
        record = {
            'Platform': tax_tx.transaction.platform,
            'Trade ID': str(tax_tx.transaction.trade_id),
            'Trading Pair': str(tax_tx.transaction.pair),
            'Base Currency': str(tax_tx.transaction.base_currency),
            'Quote Currency': str(tax_tx.transaction.quote_currency),
            'Price': float(tax_tx.transaction.price),  # Convert Decimal to float
            'Date & Time': tax_tx.transaction.time.strftime('%Y-%m-%d %H:%M:%S'),
            'Volume': float(tax_tx.transaction.vol),  # Convert Decimal to float
            'Total Cost': float(tax_tx.transaction.cost),  # Convert Decimal to float
            'Fee': float(tax_tx.transaction.fee),  # Convert Decimal to float
            'Type': str(tax_tx.transaction.type).upper(),
            f'Exchange Rate (Quote Currency/PLN)': float(tax_tx.tax_exchange_rate.rate),  # Convert Decimal to float
            'Rate Date': tax_tx.tax_exchange_rate.rateDate.strftime('%Y-%m-%d'),
            'Total Cost (PLN)': ''  # Placeholder for the calculated column
        }
        df_records.append(record)
    
    df = pd.DataFrame(df_records)
    
    # Set numeric columns type explicitly
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee', 'Exchange Rate (Quote Currency/PLN)']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])
    
    return df

def save_trades(trades: List[TransactionForTax]):
    """Save trades to JSON and CSV formats."""
    df = _create_dataframe(trades)
    
    # Save to JSON using pandas to_json
    df.to_json("tax_transactions.json", orient='records', indent=4)

    # Save to CSV
    df.to_csv("tax_transactions.csv", index=False)
    
    logger.info("Saved tax transactions to tax_transactions.json and tax_transactions.csv")

def save_trades_to_excel(trades: List[TransactionForTax], filename: str = "tax_transactions.xlsx"):
    """
    Save trades to Excel with color formatting.
    """
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
    number_format = workbook.add_format({'num_format': '#.##0,00000000'})  # For crypto values
        
    # Set numeric format for specific columns
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee', 'Exchange Rate (Quote Currency/PLN)', 'Total Cost (PLN)']
    for col_name in numeric_columns:
        col_idx = df.columns.get_loc(col_name)
        worksheet.set_column(col_idx, col_idx, None, number_format)
    
    # Get the column letters for the formula
    total_cost_col = df.columns.get_loc('Total Cost') + 1
    fee_col = df.columns.get_loc('Fee') + 1
    exchange_rate_col = df.columns.get_loc('Exchange Rate (Quote Currency/PLN)') + 1
    type_col = df.columns.get_loc('Type') + 1

    # Add the Total Cost (PLN) column header and format
    last_col = len(df.columns) - 1
    
    # Add formula for each row starting from row 2 (1-based in Excel)
    for row in range(2, len(df) + 2):
        formula = (f'=IF(${chr(64+type_col)}{row}="BUY",'
                  f'(${chr(64+total_cost_col)}{row}+${chr(64+fee_col)}{row})*'
                  f'${chr(64+exchange_rate_col)}{row},'
                  f'(${chr(64+total_cost_col)}{row}-${chr(64+fee_col)}{row})*'
                  f'${chr(64+exchange_rate_col)}{row})')
        worksheet.write_formula(row-1, last_col, formula)
    
    # Apply conditional formatting
    worksheet.conditional_format(1, 0, len(df), last_col, {
        'type': 'formula',
        'criteria': f'=${chr(64+type_col)}2="BUY"',
        'format': buy_format
    })
    worksheet.conditional_format(1, 0, len(df), last_col, {
        'type': 'formula',
        'criteria': f'=${chr(64+type_col)}2="SELL"',
        'format': sell_format
    })
    
    # Auto-adjust columns width
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = max(
            series.astype(str).map(len).max(),
            len(str(series.name))
        ) + 1
        worksheet.set_column(idx, idx, max_len)
    
    # Auto-adjust the new PLN column
    worksheet.set_column(last_col, last_col, 15)
    
    writer.close()
    logger.info(f"Saved tax transactions to {filename}")
