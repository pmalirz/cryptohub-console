import logging
from decimal import Decimal
from dataclasses import asdict
from typing import List

import pandas as pd

from nbp import NBPClient
from tax_processor import create_tax_transactions, calculate_pit_38
from transaction import TransactionForTax

# Import Rich components for user-facing output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

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
            'Total Cost (PLN)': float(tax_tx.total_cost_tax_curr),
            'Total Cost (PLN) by Formula': ''  # Placeholder for the calculated column            
        }
        df_records.append(record)
    
    df = pd.DataFrame(df_records)
    
    # Set numeric columns type explicitly
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee', 'Exchange Rate (Quote Currency/PLN)', 'Total Cost (PLN)', 'Total Cost (PLN) by Formula']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])
    
    return df

def save_trades_to_excel(trades: List[TransactionForTax], filename: str = "trades_taxpl.xlsx"):
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
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee', 'Exchange Rate (Quote Currency/PLN)', 'Total Cost (PLN)', 'Total Cost (PLN) by Formula']
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
    
    writer.close()
    
    colored_filename = f"[blue]{filename}[/blue]"
    logger.info(f"Saved tax transactions to {colored_filename}. You can open the file to make your own analysis and calculations.")
    
    # User-friendly message using Rich
    console.print(Panel(f"Saved tax transactions to {colored_filename}.\nOpen the file to review your analysis!",
                          title="Excel File Saved", border_style="green"))


def process_pit38_tax(config, trades):
    # Get exchange rates from NBP
    nbp = NBPClient()
    rates = nbp.get_rates_for_transactions(transactions=trades)
    logger.info("NBP downloaded successfully")
    
    # Create transactions model for tax calculation
    tax_transactions = create_tax_transactions(trades, rates, config.settlement_day)
    logger.info(f"Mapped {len(tax_transactions)} transactions with rates")
    
    # Save tax transactions model to file
    save_trades_to_excel(tax_transactions)
    
    # Calculate PIT-38 tax
    pit38 = calculate_pit_38(tax_transactions, config.tax_year, Decimal('0.00'))
    
    logger.info(f"PIT-38 Calculations for tax year {config.tax_year}:")
    
    field_descriptions = {
        "year": "Tax year",
        "field34_income": "Field 34: Total income from crypto sales",
        "field35_costs_current_year": "Field 35: Costs from current year",
        "field36_costs_previous_years": "Field 36: Unused costs from previous years ",
        "field37_tax_base": "Field 37: Taxable income (if positive)",
        "field38_loss": "Field 38: Loss (if negative)",
        "field39_tax": "Field 39: Tax due (19% of field 37)"
    }
    
    # Log details and also prepare data for user display
    table = Table(title=f"PIT-38 Calculations for Tax Year {config.tax_year}")
    table.add_column("Description", justify="left")
    table.add_column("Value", justify="right")
    
    for field_name, value in asdict(pit38).items():
        description = field_descriptions.get(field_name, field_name)
        logger.info(f"{description}: {value}")
        # Apply red color to Field 39
        if field_name == "field39_tax":
            value_str = f"[red]{value}[/red]"
        else:
            value_str = str(value)
        table.add_row(description, value_str)

    # Display the calculations in a nicely formatted table using Rich
    console.print(table, emoji=True)
    
    return pit38