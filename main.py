from dataclasses import asdict
from decimal import Decimal
from addin_taxpl import process_pit38_tax
from addin_trades import download_and_save_trades
from config import load_config
from banner import display_banner
from help import display_help
from kraken import KrakenAPI
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

    # Download trades from Kraken
    trades = download_and_save_trades(config)
    
    # Process PIT-38 tax calculations
    process_pit38_tax(config, trades)    
    
    
if __name__ == "__main__":
    main()

