import sys
import logging
from colorama import init
from rich.console import Console
from rich.panel import Panel

from .config import load_config
from .banner import display_banner
from .help import display_help
from . import set_logging
from .menu import interactive_menu

# Initialize colorama and logging
init(autoreset=True)
set_logging.setup_logging()
logger = logging.getLogger(__name__)
console = Console()


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
