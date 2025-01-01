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
    while True:
        console.print("[bold blue]Welcome to CryptoHub Interactive Menu[/bold blue]")
        
        action = questionary.select(
            "Choose an action:",
            choices=[
                "Download Trades",
                "Calculate Tax (PL Only)",
                "Exit"
            ],
            use_indicator=True,
            style=questionary.Style([
                ('selected', 'bg:blue fg:white'),
                ('pointer', 'fg:blue'),
            ])
        ).ask()
        
        if action == "Download Trades":
            # Gather available account names
            account_choices = []
            kraken_accounts = list(config.kraken_accounts.values())
            binance_accounts = list(config.binance_accounts.values())
            
            logger.debug(f"Found {len(kraken_accounts)} Kraken accounts")
            logger.debug(f"Found {len(binance_accounts)} Binance accounts")
            
            for acc in kraken_accounts:
                account_choices.append(f"Kraken: {acc.name}")
            for acc in binance_accounts:
                account_choices.append(f"Binance: {acc.name}")
            
            if not account_choices:
                console.print("[red]No accounts available to download trades from![/red]")
                continue
                
            # Show account selection with checkbox (multi-select) and Back option
            console.print("\n[bold yellow]Select accounts to download:[/bold yellow]")
            choices = ["Back to Main Menu", "All Accounts"] + account_choices
            chosen = questionary.checkbox(
                "Select accounts (space to toggle, enter to confirm):",
                choices=choices,
                style=questionary.Style([
                    ('selected', 'bg:blue fg:white'),
                    ('checkbox', 'fg:yellow'),
                    ('pointer', 'fg:blue'),
                ])
            ).ask()
            
            # Check if user wants to go back or no selection made
            if not chosen or "Back to Main Menu" in chosen:
                logger.debug("User chose to return to main menu")
                continue
            
            # Create a fresh config copy to avoid modifying the original
            working_config = config.copy()
            
            if "All Accounts" not in chosen:
                # Filter the configuration to include only the selected accounts
                filtered_kraken = {
                    k: v for k, v in working_config.kraken_accounts.items() 
                    if f"Kraken: {v.name}" in chosen
                }
                filtered_binance = {
                    k: v for k, v in working_config.binance_accounts.items() 
                    if f"Binance: {v.name}" in chosen
                }
                working_config.kraken_accounts = filtered_kraken
                working_config.binance_accounts = filtered_binance
                logger.debug(f"Filtered to {len(filtered_kraken)} Kraken and {len(filtered_binance)} Binance accounts")
            
            # Verify we have accounts to work with
            if not working_config.hasAnyAccounts():
                console.print("[red]No valid accounts selected![/red]")
                continue
            
            # Download trades
            trades = download_and_save_trades(working_config)
            
            # Return to main menu
            continue
    
        elif action == "Calculate Tax (PL Only)":
            trades = download_and_save_trades(config)
            process_pit38_tax(config, trades)
            continue
        
        elif action == "Exit":
            console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)

def main():
    display_banner()
    
    if len(sys.argv) == 2 and sys.argv[1] in ['/?', '--help', '-h']:
        display_help()
        return

    try:
        config = load_config()
        
        if not config.hasAnyAccounts():
            logger.error("API credentials for trading platforms missing.")
            error_message = (
                "API credentials for trading platforms are missing.\n\n"
                "Please refer to /? help for details on setting up your credentials."
            )
            console.print(Panel(error_message, title="Configuration Error", border_style="red"))
            return

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