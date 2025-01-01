from dataclasses import asdict
from decimal import Decimal
from config import load_config
from banner import display_banner
from help import display_help
from kraken import KrakenAPI
from file_store import save_trades_to_excel
from nbp import NBPClient
import logging
from colorama import init, Fore
import set_logging
from tax_processor import calculate_pit_38, create_tax_transactions
import sys

# Initialize colorama
init(autoreset=True)

# Initialize the logging configuration
set_logging.setup_logging()

logger = logging.getLogger(__name__)

def main():        
    display_banner()
    
    # Display help if requested
    if len(sys.argv) == 2 and sys.argv[1] in ['/?', '--help', '-h']:
        display_help()
        return    
    
    # Load configuration
    config = load_config()
    if not config.hasAnyKrakenAccounts():
        logger.error("API credentials for Kraken account missing.")
        logger.error("Please provide them in .env file or via CLI arguments:")
        logger.error("  cryptotaxpl --KRAKEN_1 \"My Account\" --KRAKEN_API_KEY_1 key --KRAKEN_API_SECRET_1 secret")
        return

    # Get Trades from all configured Kraken accounts
    trades = []
    for account_id, account in config.kraken_accounts.items():
        kraken = KrakenAPI(account.api_key, account.api_secret, account.name)
        account_trades = kraken.download_all_trades()
        trades.extend(account_trades)
        logger.info(f"Trades downloaded successfully for account: {account.name if account.name else 'Unnamed Account'}")
    
    #Get exchange rates from NBP
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
    logger.info("﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")
    logger.info(f"PIT-38 Calculations for tax year {config.tax_year}:")
    field_descriptions = {
        "year": "✔️ Tax year 📅",
        "field34_income": "✔️ Field 34: Total income from crypto sales 💰",
        "field35_costs_current_year": "✔️ Field 35: Costs from current year 💸",
        "field36_costs_previous_years": "✔️ Field 36: Unused costs from previous years 📉",
        "field37_tax_base": "✔️ Field 37: Taxable income (if positive) 🧾",
        "field38_loss": "✔️ Field 38: Loss (if negative) 📉",
        "field39_tax": "✔️ Field 39: Tax due (19% of field 37) 💳"
    }
    for field_name, value in asdict(pit38).items():
        description = field_descriptions.get(field_name, field_name)
        logger.info(f"{description}: {value}")        
    logger.info("﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")    
    
    
if __name__ == "__main__":
    main()

