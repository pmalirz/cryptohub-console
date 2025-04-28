import sys
import logging
from colorama import init
from rich.console import Console
from rich.panel import Panel

from .config import load_config
from .banner import display_banner
from .help import display_help
from . import set_logging
from .menu import MenuManager

# Initialize colorama and logging
init(autoreset=True)
set_logging.setup_logging()
logger = logging.getLogger(__name__)
console = Console()


def main(argv=None, exit_fn=sys.exit):
    """Main entry point with injectable dependencies for testing."""
    if argv is None:
        argv = sys.argv

    display_banner()

    if len(argv) == 2 and argv[1] in ['/?', '--help', '-h']:
        display_help()
        return 0

    try:
        config = load_config()

        if not config.hasAnyAccounts():
            logger.error("API credentials for trading platforms missing.")
            error_message = (
                "API credentials for trading platforms are missing.\n\n"
                "Please refer to /? help for details on setting up your credentials."
            )
            console.print(Panel(error_message, title="Configuration Error", border_style="red"))
            return 1

        # Use MenuManager for interactive menu
        menu_manager = MenuManager(console=console, exit_fn=exit_fn)
        menu_manager.interactive_menu(config)
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/yellow]")
        return 0
    except Exception as e:
        logger.exception("An unexpected error occurred")
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
