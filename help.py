from colorama import Fore, Style, init
import logging

# Initialize colorama
init(autoreset=True)

logger = logging.getLogger(__name__)

def display_help():
    """Display colorful help information about configuration parameters."""
    
    # Header
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}CryptoTaxPL Configuration Guide")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}\n")
    
    # Environment Variables Section
    print(f"{Fore.GREEN}{Style.BRIGHT}1. Environment Variables (.env file){Style.RESET_ALL}")
    print("Create a .env file in the project root directory with the following parameters:\n")
    
    env_vars = [
        ("KRAKEN_1", "Optional account name", "My Kraken Account"),
        ("KRAKEN_API_KEY_1", "Required API key", "your_api_key_here"),
        ("KRAKEN_API_SECRET_1", "Required API secret", "your_api_secret_here"),
        ("SETTLEMENT_DAY", "Settlement day for tax calculations (default: -1)", "-1"),
        ("TAX_YEAR", "Required tax year", "2024")
    ]
    
    for var, desc, example in env_vars:
        print(f"{Fore.YELLOW}{var}{Style.RESET_ALL}: {desc}")
        print(f"  {Fore.BLUE}Example: {var}={example}{Style.RESET_ALL}\n")
    
    # Multiple Accounts Section
    print(f"{Fore.GREEN}{Style.BRIGHT}2. Multiple Accounts Configuration{Style.RESET_ALL}")
    print("Configure multiple accounts by incrementing the number:\n")
    
    print(f"{Fore.YELLOW}KRAKEN_1{Style.RESET_ALL}=First Account")
    print(f"{Fore.YELLOW}KRAKEN_API_KEY_1{Style.RESET_ALL}=first_key")
    print(f"{Fore.YELLOW}KRAKEN_API_SECRET_1{Style.RESET_ALL}=first_secret\n")
    print(f"{Fore.YELLOW}KRAKEN_2{Style.RESET_ALL}=Second Account")
    print(f"{Fore.YELLOW}KRAKEN_API_KEY_2{Style.RESET_ALL}=second_key")
    print(f"{Fore.YELLOW}KRAKEN_API_SECRET_2{Style.RESET_ALL}=second_secret\n")
    
    # Command Line Arguments Section
    print(f"{Fore.GREEN}{Style.BRIGHT}3. Command Line Arguments{Style.RESET_ALL}")
    print("Override .env values using command line arguments:\n")
    
    cli_examples = [
        ("Set tax year", "python main.py --TAX_YEAR 2024"),
        ("Set settlement day", "python main.py --SETTLEMENT_DAY -1"),
        ("Override Kraken account", "python main.py --KRAKEN_1 \"My Account\" --KRAKEN_API_KEY_1 key --KRAKEN_API_SECRET_1 secret")
    ]
    
    for desc, cmd in cli_examples:
        print(f"{Fore.YELLOW}{desc}:{Style.RESET_ALL}")
        print(f"  {Fore.BLUE}{cmd}{Style.RESET_ALL}\n")
    
    # Configuration Priority Section
    print(f"{Fore.GREEN}{Style.BRIGHT}4. Configuration Priority{Style.RESET_ALL}")
    priorities = [
        "1. Command line arguments (highest priority)",
        "2. Environment variables from .env file",
        "3. Default values (lowest priority)"
    ]
    
    for priority in priorities:
        print(f"{Fore.YELLOW}{priority}{Style.RESET_ALL}")
    print()
    
    # Required Parameters Section
    print(f"{Fore.GREEN}{Style.BRIGHT}5. Required Parameters{Style.RESET_ALL}")
    required = [
        "• TAX_YEAR must be provided either in .env or via command line",
        "• At least one Kraken account must be configured with API key and secret"
    ]
    
    for req in required:
        print(f"{Fore.RED}{req}{Style.RESET_ALL}")
    print()

