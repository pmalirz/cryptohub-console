import logging
from decimal import Decimal
from dataclasses import asdict
from typing import List
from datetime import datetime
from pathlib import Path
import os

import pandas as pd
import questionary

from .nbp import NBPClient
from .tax_processor import create_tax_transactions, calculate_pit_38
from .transaction import Transaction, TransactionForTax

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

def _create_dataframe(trades: list[TransactionForTax]) -> pd.DataFrame:
    """Create a DataFrame from tax transactions."""
    df_records = []
    for tax_tx in trades:
        record = {
            'Platform': tax_tx.transaction.platform,
            'Trade ID': str(tax_tx.transaction.trade_id),
            'Trading Pair': str(tax_tx.transaction.trading_pair),
            'Base Currency': str(tax_tx.transaction.base_currency),
            'Quote Currency': str(tax_tx.transaction.quote_currency),
            'Price': float(tax_tx.transaction.price),
            'Date & Time': tax_tx.transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Volume': float(tax_tx.transaction.volume),
            'Total Cost': float(tax_tx.transaction.total_cost),
            'Fee': float(tax_tx.transaction.fee),
            'Type': str(tax_tx.transaction.trade_type).upper(),
            'Exchange Rate (Quote Currency/PLN)': float(tax_tx.tax_exchange_rate.rate),
            'Rate Date': tax_tx.tax_exchange_rate.rate_date.strftime('%Y-%m-%d'),
            'Total Cost (PLN)': float(tax_tx.total_cost_tax_currency),
            'Total Cost (PLN) by Formula': ''  # Placeholder for the calculated column            
        }
        df_records.append(record)
    
    df = pd.DataFrame(df_records)
    
    # Set numeric columns type explicitly
    numeric_columns = ['Price', 'Volume', 'Total Cost', 'Fee', 'Exchange Rate (Quote Currency/PLN)', 'Total Cost (PLN)', 'Total Cost (PLN) by Formula']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])
    
    return df

def save_trades_to_excel(trades: List[TransactionForTax], filename: str = "taxpl.xlsx"):
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
    logger.info(f"Saved trades together with tax calculations to {colored_filename}.")
    
    # User-friendly message using Rich
    console.print(f"💾 Saved trades together with tax calculations to {colored_filename}.")

def load_trades_from_excel(filename: str = "trades.xlsx") -> list[Transaction]:
    """Load trades from Excel file and convert to Transaction objects."""
    try:
        df = pd.read_excel(filename)
        logger.info(f"Successfully loaded {len(df)} trades from {filename}")
        
        transactions = []
        for _, row in df.iterrows():
            transaction = Transaction(
                platform=row['Platform'],
                trade_id=str(row['Trade ID']),
                trading_pair=str(row['Trading Pair']),
                base_currency=str(row['Base Currency']),
                quote_currency=str(row['Quote Currency']),
                price=Decimal(str(row['Price'])),
                timestamp=datetime.strptime(row['Date & Time'], '%Y-%m-%d %H:%M:%S'),
                volume=Decimal(str(row['Volume'])),
                total_cost=Decimal(str(row['Total Cost'])),
                fee=Decimal(str(row['Fee'])),
                trade_type=str(row['Type'])
            )
            transactions.append(transaction)
            
        return transactions
        
    except FileNotFoundError:
        logger.error(f"File {filename} not found")
        raise
    except Exception as e:
        logger.error(f"Error loading trades from {filename}: {e}")
        raise

def get_recent_trade_files(pattern: str = "trades_*.xlsx", limit: int = 5) -> list[str]:
    """Get most recent trade files matching the pattern."""
    # Get all files matching the pattern
    files = list(Path('.').glob(pattern))
    # Sort by modification time, newest first
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    # Return only the specified number of files
    return [f.name for f in files[:limit]]

def process_pit38_tax(config):
    """Process PIT-38 tax calculations based on trades from Excel file."""
    console.rule("[bold blue]🇵🇱 PIT-38 Tax Calculation[/bold blue]")
    
    # Get recent trade files
    recent_files = get_recent_trade_files()
    
    # Create choices for questionary
    choices = ["Enter file name manually", "trades.xlsx"] + recent_files
    
    file_choice = questionary.select(
        "Select trades file or enter manually:",
        choices=choices,
        use_indicator=True,
        style=questionary.Style([
            ('selected', 'bg:blue fg:white'),
            ('pointer', 'fg:blue'),
        ])
    ).ask()
    
    if file_choice == "Enter file name manually":
        filename = questionary.text(
            "Enter trades file name:",
            default="trades.xlsx"
        ).ask()
    elif file_choice == "trades.xlsx":
        filename = "trades.xlsx"
    else:
        filename = file_choice
    
    try:
        trades = load_trades_from_excel(filename)
        console.print(f"[green]Successfully loaded {len(trades)} trades from {filename}[/green]")
    except FileNotFoundError:
        console.print(f"[red]Error: File {filename} not found![/red]")
        return
    except Exception as e:
        console.print(f"[red]Error loading trades: {str(e)}[/red]")
        return
        
    # Get exchange rates from NBP with a progress bar
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    nbp = NBPClient()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True
    ) as progress:
        task = progress.add_task("Downloading NBP rates for all trades...📈", total=None)
        rates = nbp.get_rates_for_transactions(transactions=trades)
    
    logger.info("NBP downloaded successfully")
    console.print("📥 [bold green]NBP rates downloaded successfully.[/bold green]")
    
    # Create transactions model for tax calculation
    tax_transactions = create_tax_transactions(trades, rates, config.settlement_day)
    logger.info(f"Mapped {len(tax_transactions)} transactions with rates")
    
    # Save tax transactions model to file
    save_trades_to_excel(tax_transactions)
    
    # Calculate PIT-38
    pit38 = calculate_pit_38(tax_transactions, config.tax_year, config.previous_year_cost_field36)
    
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
    
    from dataclasses import asdict
    for field_name, value in asdict(pit38).items():
        description = field_descriptions.get(field_name, field_name)
        logger.info(f"{description}: {value}")
        value_str = f"[red]{value}[/red]" if field_name == "field39_tax" else str(value)
        table.add_row(description, value_str)
    
    console.print(table, emoji=True)
    
    return pit38