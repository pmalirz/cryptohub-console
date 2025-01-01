from dataclasses import asdict
from decimal import Decimal
from config import load_config
from banner import display_banner
from kraken import KrakenAPI
from file_store import save_trades_to_excel
from nbp import NBPClient
import logging
from colorama import init, Fore
import set_logging
from tax_processor import calculate_pit_38, create_tax_transactions

# Initialize colorama
init(autoreset=True)

# Initialize the logging configuration
set_logging.setup_logging()

logger = logging.getLogger(__name__)

def main():
    display_banner()
    logger.info("Starting the main function")
    config = load_config()
    if not config["krakenKey"] or not config["krakenSecret"]:
        logger.error("API credentials missing. Please provide them in .env file or via CLI arguments.")
        return

    kraken = KrakenAPI(config["krakenKey"], config["krakenSecret"])
    
    trades = kraken.download_all_trades()
    logger.info("Trades downloaded successfully")
    
    nbp = NBPClient()

    rates = nbp.get_rates_for_transactions(transactions=trades)
    logger.info("NBP downloaded successfully")
    
    tax_transactions = create_tax_transactions(trades, rates, config["settlementDay"])
    logger.info(f"Mapped {len(tax_transactions)} transactions with rates")
    
    # Save tax transactions to file
    save_trades_to_excel(tax_transactions)
    
    pit38 = calculate_pit_38(tax_transactions, config["taxYear"], Decimal('0.00'))
    logger.info("﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")
    logger.info(f"PIT-38 Calculations for tax year {config['taxYear']}:")
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

