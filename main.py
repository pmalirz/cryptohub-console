from config import load_config
from kraken import KrakenAPI
from file_store import save_trades
from nbp import NBPClient
import logging
from colorama import init, Fore, Style
from datetime import datetime, timedelta
import json
import set_logging
from tax_processor import create_tax_transactions
from transaction import Transaction, TransactionForTax, ExchangeRate

# Initialize colorama
init(autoreset=True)

# Initialize the logging configuration
set_logging.setup_logging()

logger = logging.getLogger(__name__)

def display_banner():
    banner = f"""
    {Fore.GREEN}############################################################
    # {Fore.LIGHTYELLOW_EX}CryptoTaxPL by {Fore.LIGHTRED_EX}Przemek Malirz {Fore.LIGHTYELLOW_EX}(p.malirz@gmail.com), 2025
    {Fore.GREEN}############################################################
    """
    print(banner)

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
    save_trades(tax_transactions)    
    
if __name__ == "__main__":
    main()