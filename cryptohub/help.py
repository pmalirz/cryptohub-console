from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

console = Console()


def display_help():
    """Display rich help information about configuration parameters."""

    # Header
    console.print(Panel.fit(
        "[bold cyan]CryptoTaxPL Configuration Guide[/]",
        border_style="cyan"
    ))

    # Environment Variables Section
    env_table = Table(show_header=True, box=box.ROUNDED)
    env_table.add_column("Variable", style="yellow")
    env_table.add_column("Description", style="white")
    env_table.add_column("Example", style="blue")

    env_vars = [
        ("KRAKEN_1", "Optional account name", "My Kraken Account"),
        ("KRAKEN_API_KEY_1", "Required API key", "your_api_key_here"),
        ("KRAKEN_API_SECRET_1", "Required API secret", "your_api_secret_here"),
        ("SETTLEMENT_DAY", "Settlement day for tax calculations (default: -1)", "-1"),
        ("TAX_YEAR", "Required tax year", "2024")
    ]

    for var, desc, example in env_vars:
        env_table.add_row(var, desc, example)

    console.print(Panel(
        env_table,
        title="[bold green]1. Environment Variables (.env file)",
        border_style="green"
    ))

    # Multiple Accounts Section
    accounts_md = """
    ## Multiple Accounts Configuration
    Configure multiple accounts by incrementing the number:
    ```env
    KRAKEN_1=First Account
    KRAKEN_API_KEY_1=first_key
    KRAKEN_API_SECRET_1=first_secret

    KRAKEN_2=Second Account
    KRAKEN_API_KEY_2=second_key
    KRAKEN_API_SECRET_2=second_secret
    ```
    """
    console.print(Panel(
        Markdown(accounts_md),
        title="[bold green]2. Multiple Accounts",
        border_style="green"
    ))

    # Command Line Arguments Section
    cli_table = Table(show_header=True, box=box.ROUNDED)
    cli_table.add_column("Action", style="yellow")
    cli_table.add_column("Command", style="blue")

    cli_examples = [
        ("Set tax year", "cryptotaxpl --TAX_YEAR 2024"),
        ("Set settlement day", "cryptotaxpl --SETTLEMENT_DAY -1"),
        ("Override Kraken account", "cryptotaxpl --KRAKEN_1 \"My Account\" --KRAKEN_API_KEY_1 key --KRAKEN_API_SECRET_1 secret"),
        ("Show this help", "cryptotaxpl --help")
    ]

    for desc, cmd in cli_examples:
        cli_table.add_row(desc, cmd)

    console.print(Panel(
        cli_table,
        title="[bold green]3. Command Line Arguments",
        border_style="green"
    ))

    # Configuration Priority Section
    priorities_md = """
    ## Configuration Priority
    1. Command line arguments (highest priority)
    2. Environment variables from .env file
    3. Default values (lowest priority)
    """
    console.print(Panel(
        Markdown(priorities_md),
        title="[bold green]4. Configuration Priority",
        border_style="green"
    ))

    # Required Parameters Section
    required_md = """
    ## Required Parameters
    - 🔴 TAX_YEAR must be provided either in .env or via command line
    - 🔴 At least one Kraken account must be configured with API key and secret
    """
    console.print(Panel(
        Markdown(required_md),
        title="[bold green]5. Required Parameters",
        border_style="red"
    ))
