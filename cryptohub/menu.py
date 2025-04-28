import logging
import questionary
import sys
from rich.console import Console

from .addin_taxpl import process_pit38_tax
from .addin_trades import download_and_save_trades

logger = logging.getLogger(__name__)
console = Console()


class MenuManager:
    """Class to manage the interactive menu functionality with injectable dependencies."""

    def __init__(self,
                 console=None,
                 questionary_module=None,
                 download_trades_fn=None,
                 process_tax_fn=None,
                 exit_fn=None):
        """Initialize with injectable dependencies to support testing."""
        self.console = console or Console()
        self.questionary = questionary_module or questionary
        self.download_trades_fn = download_trades_fn or download_and_save_trades
        self.process_tax_fn = process_tax_fn or process_pit38_tax
        self.exit_fn = exit_fn or sys.exit

    def get_account_choices(self, config):
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

    def filter_selected_accounts(self, config, chosen_accounts):
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

    def select_accounts(self, config, allow_all=True):
        """Present account selection UI and return selected accounts."""
        account_choices = self.get_account_choices(config)

        if not account_choices:
            self.console.print("[red]No accounts available to download trades from![/red]")
            return None

        # First, show a simple selection menu
        self.console.print("\n[bold yellow]Download trades options:[/bold yellow]")
        choices = ["Back to Main Menu"]
        if allow_all:
            choices.append("All Accounts")
        choices.append("Select Specific Accounts")

        selection = self.questionary.select(
            "Choose an option:",
            choices=choices,
            style=self.questionary.Style([
                ('selected', 'bg:blue fg:white'),
                ('pointer', 'fg:blue'),
            ])
        ).ask()

        if selection == "Back to Main Menu" or selection is None:
            logger.debug("User chose to return to main menu")
            return None

        if selection == "All Accounts":
            return ["All Accounts"]

        # Show account selection with checkbox (multi-select)
        self.console.print("\n[bold yellow]Select accounts to download:[/bold yellow]")
        chosen = self.questionary.checkbox(
            "Select accounts (space to toggle, enter to confirm):",
            choices=account_choices,
            style=self.questionary.Style([
                ('selected', 'bg:blue fg:white'),
                ('checkbox', 'fg:yellow'),
                ('pointer', 'fg:blue'),
            ])
        ).ask()

        # If user didn't select any accounts, return None
        if not chosen:
            self.console.print("[yellow]No accounts selected, returning to main menu.[/yellow]")
            return None

        return chosen

    def handle_download_trades(self, config):
        """Handle the 'Download Trades' menu option."""
        chosen = self.select_accounts(config)
        if chosen is None:
            return

        # Filter configuration to selected accounts
        working_config = self.filter_selected_accounts(config, chosen)

        # Verify we have accounts to work with
        if not working_config.hasAnyAccounts():
            self.console.print("[red]No valid accounts selected![/red]")
            return

        # Download and save trades
        self.download_trades_fn(working_config)
        return True

    def interactive_menu(self, config):
        """Display interactive menu and handle user choices."""
        menu_style = self.questionary.Style([
            ('selected', 'bg:blue fg:white'),
            ('pointer', 'fg:blue'),
        ])

        while True:
            self.console.print("[bold blue]Welcome to CryptoHub Interactive Menu[/bold blue]")

            action = self.questionary.select(
                "Choose an action:",
                choices=[
                    "Download Trades",
                    "Calculate Tax (PL Only)",
                    "Exit"
                ],
                use_indicator=True,
                style=menu_style
            ).ask()

            try:
                if action == "Download Trades":
                    self.handle_download_trades(config)
                elif action == "Calculate Tax (PL Only)":
                    self.process_tax_fn(config)
                elif action == "Exit":
                    self.console.print("[yellow]Goodbye![/yellow]")
                    self.exit_fn(0)
            except KeyboardInterrupt:
                # Properly break out of the loop when KeyboardInterrupt is caught
                self.console.print("[yellow]Operation interrupted![/yellow]")
                break  # This is the fix - adding a break to exit the while loop


# For backward compatibility and as entry points for other modules
def interactive_menu(config):
    """Entry point for the interactive menu system."""
    MenuManager(console=console).interactive_menu(config)
