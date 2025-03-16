import logging
import questionary
import sys
from rich.console import Console

from .addin_taxpl import process_pit38_tax
from .addin_trades import download_and_save_trades

logger = logging.getLogger(__name__)
console = Console()


def get_account_choices(config):
    """Get formatted list of available trading accounts."""
    account_choices = []
    kraken_accounts = list(config.kraken_accounts.values())
    binance_accounts = list(config.binance_accounts.values())

    logger.debug(f"Found {len(kraken_accounts)} Kraken accounts")
    logger.debug(f"Found {len(binance_accounts)} Binance accounts")

    for acc in kraken_accounts:
        account_choices.append(f"Kraken: {acc.name}")
    for acc in binance_accounts:
        account_choices.append(f"Binance: {acc.name}")

    return account_choices


def filter_selected_accounts(config, chosen_accounts):
    """Filter config to include only selected accounts."""
    working_config = config.copy()

    if "All Accounts" not in chosen_accounts:
        filtered_kraken = {
            k: v for k, v in working_config.kraken_accounts.items()
            if f"Kraken: {v.name}" in chosen_accounts
        }
        filtered_binance = {
            k: v for k, v in working_config.binance_accounts.items()
            if f"Binance: {v.name}" in chosen_accounts
        }
        working_config.kraken_accounts = filtered_kraken
        working_config.binance_accounts = filtered_binance
        logger.debug(f"Filtered to {len(filtered_kraken)} Kraken and {len(filtered_binance)} Binance accounts")

    return working_config


def handle_download_trades(config):
    """Handle the 'Download Trades' menu option."""
    account_choices = get_account_choices(config)

    if not account_choices:
        console.print("[red]No accounts available to download trades from![/red]")
        return

    # First, show a simple selection menu
    console.print("\n[bold yellow]Download trades options:[/bold yellow]")
    selection = questionary.select(
        "Choose an option:",
        choices=[
            "Back to Main Menu",
            "All Accounts",
            "Select Specific Accounts",
        ],
        style=questionary.Style([
            ('selected', 'bg:blue fg:white'),
            ('pointer', 'fg:blue'),
        ])
    ).ask()

    if selection == "Back to Main Menu" or selection is None:
        logger.debug("User chose to return to main menu")
        return

    chosen = []
    if selection == "All Accounts":
        chosen = ["All Accounts"]
    elif selection == "Select Specific Accounts":
        # Show account selection with checkbox (multi-select)
        console.print("\n[bold yellow]Select accounts to download:[/bold yellow]")
        chosen = questionary.checkbox(
            "Select accounts (space to toggle, enter to confirm):",
            choices=account_choices,
            style=questionary.Style([
                ('selected', 'bg:blue fg:white'),
                ('checkbox', 'fg:yellow'),
                ('pointer', 'fg:blue'),
            ])
        ).ask()

        # If user didn't select any accounts, return to main menu
        if not chosen:
            console.print("[yellow]No accounts selected, returning to main menu.[/yellow]")
            return

    # Filter configuration to selected accounts
    working_config = filter_selected_accounts(config, chosen)

    # Verify we have accounts to work with
    if not working_config.hasAnyAccounts():
        console.print("[red]No valid accounts selected![/red]")
        return

    # Download and save trades
    download_and_save_trades(working_config)


def interactive_menu(config):
    """Display interactive menu and handle user choices."""
    menu_style = questionary.Style([
        ('selected', 'bg:blue fg:white'),
        ('pointer', 'fg:blue'),
    ])

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
            style=menu_style
        ).ask()

        if action == "Download Trades":
            handle_download_trades(config)
        elif action == "Calculate Tax (PL Only)":
            process_pit38_tax(config)
        elif action == "Exit":
            console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)
