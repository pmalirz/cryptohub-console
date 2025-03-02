import logging
from decimal import Decimal
from typing import List
from datetime import datetime
from pathlib import Path

import pandas as pd
import questionary

from cryptohub.config import Configuration

from .nbp import NBPClient
from .tax_processor import create_tax_transactions, calculate_pit_38
from .transaction import Transaction, TransactionForTax

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()

# Add at the top of the file with other constants
DEFAULT_TRADES_FILE = "trades.xlsx"

# Define custom style for questionary prompts
QUESTIONARY_STYLE = questionary.Style([
    ('selected', 'bg:blue fg:white'),
    ('pointer', 'fg:blue'),
])


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


def _adjust_column_widths(worksheet, df):
    """Adjust column widths based on content."""
    for idx, col in enumerate(df.columns):
        # Get maximum length of column content
        max_length = max(
            df[col].astype(str).apply(len).max(),  # max length of values
            len(str(col))  # length of column header
        )
        # Add some padding
        adjusted_width = max_length + 4
        # Set column width with minimum and maximum constraints
        worksheet.set_column(idx, idx, min(max(adjusted_width, 8), 50))


def save_trades_to_excel(trades: List[TransactionForTax], filename: str = "taxpl.xlsx", pit38: object = None, tax_year: int = None):
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
        worksheet.write_formula(row - 1, last_col, formula)

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

    # Add tax summary if pit38 and tax_year are provided
    if pit38 is not None:
        _add_tax_summary(writer, pit38, pit38.year)  # Use pit38.year instead of tax_year parameter

    # Define formats with Polish locale
    buy_format = workbook.add_format({
        'bg_color': '#C6EFCE',  # Light green
        'num_format': '#,##0.00'  # Basic number format
    })

    sell_format = workbook.add_format({
        'bg_color': '#FFC7CE',  # Light red
        'num_format': '#,##0.00'  # Basic number format
    })

    # Create specific formats for different types of numbers
    price_volume_format = workbook.add_format({
        'num_format': '#,##0.00000000',  # 8 decimal places for crypto
        'align': 'right'
    })

    cost_format = workbook.add_format({
        'num_format': '#,##0.00',  # 2 decimal places for fiat
        'align': 'right'
    })

    pln_format = workbook.add_format({
        'num_format': '#,##0.00 "PLN"',  # PLN currency format
        'align': 'right'
    })

    # Map columns to their specific formats
    column_formats = {
        'Price': price_volume_format,
        'Volume': price_volume_format,
        'Total Cost': cost_format,
        'Fee': price_volume_format,
        'Exchange Rate (Quote Currency/PLN)': cost_format,
        'Total Cost (PLN)': pln_format,
        'Total Cost (PLN) by Formula': pln_format
    }

    # Apply formats to specific columns
    for col_name, format_obj in column_formats.items():
        if col_name in df.columns:
            col_idx = df.columns.get_loc(col_name)
            worksheet.set_column(col_idx, col_idx, None, format_obj)

    # Adjust column widths after all formatting is done
    _adjust_column_widths(worksheet, df)

    writer.close()

    colored_filename = f"[blue]{filename}[/blue]"
    logger.info(f"Saved trades together with tax calculations to {colored_filename}.")

    # User-friendly message using Rich
    console.print(f"💾 Saved trades together with tax calculations to {colored_filename}.")


def _add_tax_summary(writer: pd.ExcelWriter, pit38: object, tax_year: int) -> None:
    """Add tax calculation summary to a new worksheet."""
    # Create a summary worksheet
    worksheet = writer.book.add_worksheet('Tax Summary')

    # Define formats
    header_format = writer.book.add_format({
        'bold': True,
        'bg_color': '#0066cc',
        'font_color': 'white',
        'align': 'center',
        'border': 1
    })

    cell_format = writer.book.add_format({
        'align': 'left',
        'border': 1
    })

    number_format = writer.book.add_format({
        'num_format': '#,##0.00 "PLN"',
        'align': 'right',
        'border': 1
    })

    tax_format = writer.book.add_format({
        'num_format': '#,##0.00 "PLN"',
        'align': 'right',
        'border': 1,
        'bold': True,
        'bg_color': '#FFC7CE'  # Light red for tax amount
    })

    # Add title
    worksheet.merge_range('A1:B1', f'PIT-38 Tax Summary for {tax_year}', header_format)

    # Set column widths
    worksheet.set_column('A:A', 50)  # Description column
    worksheet.set_column('B:B', 20)  # Value column

    # Headers for the data
    worksheet.write('A2', 'Description', header_format)
    worksheet.write('B2', 'Value', header_format)

    # Tax calculation data
    tax_data = [
        ("Tax year", tax_year, cell_format),
        ("Field 34: Total income from crypto sales (PLN)", pit38.field34_income, number_format),
        ("Field 35: Costs from current year (PLN)", pit38.field35_costs_current_year, number_format),
        ("Field 36: Unused costs from previous years (PLN)", pit38.field36_costs_previous_years, number_format),
        ("Field 37: Taxable income (PLN)", pit38.field37_tax_base, number_format),
        ("Field 38: Loss (PLN)", pit38.field38_loss, number_format),
        ("Field 39: Tax due - 19% (PLN)", pit38.field39_tax, tax_format)
    ]

    # Write data
    for row, (desc, value, fmt) in enumerate(tax_data, start=2):
        worksheet.write(row, 0, desc, cell_format)
        worksheet.write(row, 1, value, fmt)

    # Set initial column widths
    worksheet.set_column('A:A', 50)  # Description column
    worksheet.set_column('B:B', 20)  # Value column

    # Create a temporary DataFrame for auto-width calculation
    summary_df = pd.DataFrame({
        'Description': [desc for desc, _, _ in tax_data],
        'Value': [value for _, value, _ in tax_data]
    })

    # Adjust column widths based on content
    _adjust_column_widths(worksheet, summary_df)


def load_trades_from_excel(filename: str = DEFAULT_TRADES_FILE) -> list[Transaction]:
    """Load trades from Excel file and convert to Transaction objects."""
    try:
        # Read Excel file with specific data types
        df = pd.read_excel(
            filename,
            dtype={
                'Platform': str,
                'Trade ID': str,
                'Trading Pair': str,
                'Base Currency': str,
                'Quote Currency': str,
                'Price': str,  # Read numbers as strings to preserve precision
                'Volume': str,
                'Total Cost': str,
                'Fee': str,
                'Type': str
            }
        )
        logger.info(f"Successfully loaded {len(df)} trades from {filename}")

        transactions = []
        for _, row in df.iterrows():
            # Convert numeric values to Decimal
            try:
                price = Decimal(row['Price'])
                volume = Decimal(row['Volume'])
                total_cost = Decimal(row['Total Cost'])
                fee = Decimal(row['Fee'])

                transaction = Transaction(
                    platform=row['Platform'],
                    trade_id=str(row['Trade ID']),
                    trading_pair=str(row['Trading Pair']),
                    base_currency=str(row['Base Currency']),
                    quote_currency=str(row['Quote Currency']),
                    price=price,
                    timestamp=datetime.strptime(row['Date & Time'], '%Y-%m-%d %H:%M:%S'),
                    volume=volume,
                    total_cost=total_cost,
                    fee=fee,
                    trade_type=str(row['Type'])
                )
                transactions.append(transaction)
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error processing row: {row}")
                logger.error(f"Error details: {str(e)}")
                raise

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


def prompt_tax_parameters(config: Configuration) -> tuple[int, int, Decimal]:
    """Prompt user for tax calculation parameters with defaults from config."""
    tax_year = questionary.text(
        "Enter tax year:",
        default=str(config.tax_year or datetime.now().year),
        validate=lambda x: x.isdigit() and int(x) > 2000,
        style=QUESTIONARY_STYLE
    ).ask()

    settlement_day = questionary.text(
        "Enter settlement day (-1 for last day of the year):",
        default=str(config.settlement_day or -1),
        validate=lambda x: x.isdigit() or (x.startswith('-') and x[1:].isdigit()),
        style=QUESTIONARY_STYLE
    ).ask()

    previous_year_cost = questionary.text(
        "Enter previous year costs from field 36:",
        default=str(config.previous_year_cost_field36 or "0.00"),
        validate=lambda x: all(part.isdigit() for part in x.replace(".", "").replace(",", "")),
        style=QUESTIONARY_STYLE
    ).ask()

    return (
        int(tax_year),
        int(settlement_day),
        Decimal(previous_year_cost.replace(",", "."))
    )


def select_trades_file(recent_files: list[str]) -> str:
    """Prompt user to select or enter trades file name."""
    choices = [f"{DEFAULT_TRADES_FILE} (default)", "Enter file name manually"] + recent_files

    file_choice = questionary.select(
        "Select trades file or enter manually:",
        choices=choices,
        default=f"{DEFAULT_TRADES_FILE} (default)",
        use_indicator=True,
        style=QUESTIONARY_STYLE
    ).ask()

    if file_choice == "Enter file name manually":
        return questionary.text(
            "Enter trades file name:",
            default=DEFAULT_TRADES_FILE,
            style=QUESTIONARY_STYLE
        ).ask()

    return DEFAULT_TRADES_FILE if file_choice == f"{DEFAULT_TRADES_FILE} (default)" else file_choice


def process_pit38_tax(config: Configuration) -> dict:
    """Process PIT-38 tax calculations based on trades from Excel file."""
    console.rule("[bold blue]🇵🇱 PIT-38 Tax Calculation[/bold blue]")

    # Get tax parameters from user
    tax_year, settlement_day, previous_year_cost = prompt_tax_parameters(config)

    # Create a temporary config with user-provided values
    working_config = config.copy()
    working_config.tax_year = tax_year
    working_config.settlement_day = settlement_day
    working_config.previous_year_cost_field36 = previous_year_cost

    # Get trades file from user
    filename = select_trades_file(get_recent_trade_files())

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
        progress.add_task("Downloading NBP rates for all trades...📈", total=None)
        rates = nbp.get_rates_for_transactions(transactions=trades)

    logger.info("NBP downloaded successfully")
    console.print("📥 [bold green]NBP rates downloaded successfully.[/bold green]")

    # Create transactions model for tax calculation
    tax_transactions = create_tax_transactions(trades, rates, working_config.settlement_day)
    logger.info(f"Mapped {len(tax_transactions)} transactions with rates")

    # Calculate PIT-38
    pit38 = calculate_pit_38(
        tax_transactions,
        working_config.tax_year,
        working_config.previous_year_cost_field36
    )

    # Save tax transactions model to file with tax summary
    save_trades_to_excel(tax_transactions, pit38=pit38)

    logger.info(f"PIT-38 Calculations for tax year {working_config.tax_year}:")

    field_descriptions = {
        "year": "Tax year",
        "field34_income": "Field 34: Total income from crypto sales (PLN)",
        "field35_costs_current_year": "Field 35: Costs from current year (PLN)",
        "field36_costs_previous_years": "Field 36: Unused costs from previous years (PLN)",
        "field37_tax_base": "Field 37: Taxable income (PLN)",
        "field38_loss": "Field 38: Loss (PLN)",
        "field39_tax": "Field 39: Tax due - 19% (PLN)"
    }

    # Log details and also prepare data for user display
    table = Table(
        title=f"PIT-38 Calculations for Tax Year {working_config.tax_year}",
        title_style="bold blue",
        header_style="bold cyan"
    )
    table.add_column("Description", justify="left", style="green")
    table.add_column("Value (PLN)", justify="right", style="yellow")

    from dataclasses import asdict
    for field_name, value in asdict(pit38).items():
        description = field_descriptions.get(field_name, field_name)
        logger.info(f"{description}: {value} PLN")
        # Format value with PLN currency for non-year fields
        if field_name != "year":
            value_str = f"{value:,.2f} PLN"
            if field_name == "field39_tax":
                value_str = f"[red]{value:,.2f} PLN[/red]"
        else:
            value_str = str(value)
        table.add_row(description, value_str)

    console.print(table, emoji=True)

    return pit38
