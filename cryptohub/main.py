import sys
import logging
import questionary
from colorama import init
from rich.console import Console
from rich.panel import Panel

from .addin_taxpl import process_pit38_tax, calculate_pit_38
from .addin_trades import download_and_save_trades
from .config import load_config
from .banner import display_banner
from .help import display_help
from . import set_logging

# Initialize colorama and logging
init(autoreset=True)
set_logging.setup_logging()
logger = logging.getLogger(__name__)
console = Console()

def interactive_menu(config):
    console.print("[bold blue]Welcome to CryptoTaxPL Interactive Menu[/bold blue]")
    
    # Main menu with arrow navigation
    action = questionary.select(
        "Choose an action:",
        choices=[
            "Download All Trades",
            "Calculate Tax (PL Only)",
            "Exit"
        ],
        use_indicator=True,
        style=questionary.Style([
            ('selected', 'bg:blue fg:white'),
            ('pointer', 'fg:blue'),
        ])
    ).ask()
    
    if action == "Download All Trades":
        # Gather available account names
        account_choices = []
        for acc in config.kraken_accounts.values():
            account_choices.append(f"Kraken: {acc.name}")
        for acc in config.binance_accounts.values():
            account_choices.append(f"Binance: {acc.name}")
        
        # Show account selection with checkbox (multi-select)
        console.print("\n[bold yellow]Select accounts to download:[/bold yellow]")
        chosen = questionary.checkbox(
            "Select accounts (space to toggle, enter to confirm):",
            choices=["All Accounts"] + account_choices,
            style=questionary.Style([
                ('selected', 'bg:blue fg:white'),
                ('checkbox', 'fg:yellow'),
                ('pointer', 'fg:blue'),
            ])
        ).ask()
        
        if chosen and "All Accounts" not in chosen:
            # Filter the configuration to include only the selected accounts
            filtered_kraken = {
                k: v for k, v in config.kraken_accounts.items() 
                if f"Kraken: {v.name}" in chosen
            }
            filtered_binance = {
                k: v for k, v in config.binance_accounts.items() 
                if f"Binance: {v.name}" in chosen
            }
            config.kraken_accounts = filtered_kraken
            config.binance_accounts = filtered_binance
        
        # Download trades and process tax calculations
        trades = download_and_save_trades(config)
        
        # Ask if user wants to calculate tax immediately
        if questionary.confirm(
            "Would you like to calculate tax for the downloaded trades?",
            default=True
        ).ask():
            process_pit38_tax(config, trades)
    
    elif action == "Calculate Tax (PL Only)":
        trades = download_and_save_trades(config)
        process_pit38_tax(config, trades)
    
    elif action == "Exit":
        console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)

def main():
    # Display banner
    display_banner()
    
    # Display help if requested
    if len(sys.argv) == 2 and sys.argv[1] in ['/?', '--help', '-h']:
        display_help()
        return

    try:
        # Load configuration
        config = load_config()
        
        if not config.hasAnyAccounts():
            logger.error("API credentials for trading platforms missing.")
            error_message = (
                "API credentials for trading platforms are missing.\n\n"
                "Please refer to /? help for details on setting up your credentials."
            )
            console.print(Panel(error_message, title="Configuration Error", border_style="red"))
            return

        # Enter interactive menu loop
        while True:
            interactive_menu(config)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.exception("An unexpected error occurred")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()

