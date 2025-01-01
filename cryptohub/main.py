from .addin_taxpl import process_pit38_tax, calculate_pit_38
from .addin_trades import download_and_save_trades
from .config import load_config
from .banner import display_banner
from .help import display_help
import logging
from colorama import init
from . import set_logging
import sys
from rich.console import Console
from rich.panel import Panel

# Initialize colorama
init(autoreset=True)

# Initialize the logging configuration
set_logging.setup_logging()

logger = logging.getLogger(__name__)
console = Console()

def main():        
    # Display banner (could be further enhanced with Rich in display_banner)
    display_banner()
    
    # Display help if requested
    if len(sys.argv) == 2 and sys.argv[1] in ['/?', '--help', '-h']:
        display_help()
        return    
    
    # Load configuration
    config = load_config()
    
    if not config.hasAnyKrakenAccounts():
        # Log errors for diagnostics
        logger.error("API credentials for Kraken account missing.")
        logger.error("Please provide them in .env file or via CLI arguments:")
        logger.error("  cryptohub --KRAKEN_1 \"My Account\" --KRAKEN_API_KEY_1 key --KRAKEN_API_SECRET_1 secret")
        
        # Show an error panel using Rich for user-friendly output
        error_message = (
            "API credentials for Kraken account missing.\n\n"
            "Please provide them in your .env file or via CLI arguments:\n"
            "  cryptohub --KRAKEN_1 \"My Account\" --KRAKEN_API_KEY_1 key --KRAKEN_API_SECRET_1 secret"
        )
        console.print(Panel(error_message, title="Configuration Error", border_style="red"))
        return

    # Download trades from Kraken (handled in the logs)
    trades = download_and_save_trades(config)
    
    # Process PIT-38 tax calculations (handled in the logs)
    process_pit38_tax(config, trades)    
    
if __name__ == "__main__":
    main()

