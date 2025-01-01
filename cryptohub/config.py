import os
from typing import Dict
from dataclasses import dataclass
import argparse
import logging
from dotenv import load_dotenv
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class KrakenAccount:
    name: str
    api_key: str
    api_secret: str
@dataclass
class BinanceAccount:
    name: str
    api_key: str
    api_secret: str
    pair_pattern: str | None 

@dataclass
class Configuration:
    kraken_accounts: Dict[str, KrakenAccount]
    binance_accounts: Dict[str, BinanceAccount]
    settlement_day: int
    tax_year: int
    previous_year_cost_field36: Decimal
    
    def hasAnyAccounts(self) -> bool:
        """
        Check if there are any accounts configured (Kraken or Binance).
        Returns True if at least one account exists, False otherwise.
        """
        return bool(self.kraken_accounts) or bool(self.binance_accounts)
    
    def copy(self) -> 'Configuration':
        """Create a deep copy of the configuration."""
        return Configuration(
            kraken_accounts=self.kraken_accounts.copy(),
            binance_accounts=self.binance_accounts.copy(),
            settlement_day=self.settlement_day,
            tax_year=self.tax_year,
            previous_year_cost_field36=self.previous_year_cost_field36
        )

def load_config() -> Configuration:
    """
    Load configuration from .env file and command line arguments.
    Command line arguments override .env values.
    Returns a typed Configuration object.
    Raises ValueError if duplicate accounts are found.
    """
    # Load environment variables first
    load_dotenv()

    # Create parser that matches .env variable names
    parser = argparse.ArgumentParser(description='CryptoTaxPL configuration')

    # Add arguments for all possible env variables for Kraken accounts
    for key in os.environ:
        if key.startswith('KRAKEN_'):
            parser.add_argument(f'--{key}', type=str, help=f'Override {key} from .env')
    # Add arguments for all possible env variables for Binance accounts
    for key in os.environ:
        if key.startswith('BINANCE_'):
            parser.add_argument(f'--{key}', type=str, help=f'Override {key} from .env')

    # Add standard configuration parameters
    parser.add_argument('--SETTLEMENT_DAY', type=int, 
                       help='Settlement day for tax calculation (default: -1)')
    parser.add_argument('--TAX_YEAR', type=int, 
                       help='Tax year for calculations (required)')
    parser.add_argument('--PREVIOUS_YEAR_COST_FIELD36', type=str, 
                       help='Previous year cost from field 36 (default: 0.00)')
    
    args, unknown = parser.parse_known_args()
    args_dict = {k: v for k, v in vars(args).items() if v is not None}

    # Start with env vars and override with command line args
    config = {
        "krakenAccounts": {},
        "binanceAccounts": {},  # Added Binance accounts container.
        "settlementDay": int(os.getenv('SETTLEMENT_DAY', '-1')),
        "taxYear": int(os.getenv('TAX_YEAR', '0')),
        "previousYearCostField36": Decimal(os.getenv('PREVIOUS_YEAR_COST_FIELD36', '0.00'))
    }

    # Override with command line arguments if provided
    if args_dict.get('SETTLEMENT_DAY') is not None:
        config['settlementDay'] = args_dict['SETTLEMENT_DAY']
    if args_dict.get('TAX_YEAR') is not None:
        config['taxYear'] = args_dict['TAX_YEAR']
    if args_dict.get('PREVIOUS_YEAR_COST_FIELD36') is not None:
        config['previousYearCostField36'] = Decimal(args_dict['PREVIOUS_YEAR_COST_FIELD36'])
    if args_dict.get('FILTER_QUOTE_ASSETS') is not None:
        config['filterQuoteAssets'] = args_dict['FILTER_QUOTE_ASSETS']
        
    # Track unique names and API keys for Kraken.
    used_names = set()
    used_api_keys = set()
    
    # Load Kraken accounts.
    i = 1
    while True:
        name = os.getenv(f'KRAKEN_{i}')
        key = os.getenv(f'KRAKEN_API_KEY_{i}')
        secret = os.getenv(f'KRAKEN_API_SECRET_{i}')
        
        # Break if no more accounts found
        if not key or not secret:
            break
            
        # Use default name if none provided
        actual_name = name or f'Kraken{i}'
        actual_key = args_dict.get(f'KRAKEN_API_KEY_{i}', key)
        
        # Check for duplicate name
        if actual_name in used_names:
            raise ValueError(f"Duplicate Kraken account name found: {actual_name}")
        
        # Check for duplicate API key
        if actual_key in used_api_keys:
            raise ValueError("Duplicate Kraken API key found")
            
        # Add to tracking sets
        used_names.add(actual_name)
        used_api_keys.add(actual_key)
            
        config['krakenAccounts'][str(i)] = {
            'name': actual_name,
            'apiKey': actual_key,
            'apiSecret': args_dict.get(f'KRAKEN_API_SECRET_{i}', secret)
        }
        i += 1

    # Track unique names and API keys for Binance.
    used_binance_names = set()
    used_binance_keys = set()
    
    # Load Binance accounts.
    i = 1
    while True:
        name = os.getenv(f'BINANCE_{i}')
        key = os.getenv(f'BINANCE_API_KEY_{i}')
        secret = os.getenv(f'BINANCE_API_SECRET_{i}')
        pair_pattern = os.getenv(f'BINANCE_PAIR_PATTERN_{i}')  # New parameter
        
        if not key or not secret:
            break
        
        actual_name = name or f'Binance{i}'
        actual_key = args_dict.get(f'BINANCE_API_KEY_{i}', key)
        
        if actual_name in used_binance_names:
            raise ValueError(f"Duplicate Binance account name found: {actual_name}")
        if actual_key in used_binance_keys:
            raise ValueError("Duplicate Binance API key found")
        
        used_binance_names.add(actual_name)
        used_binance_keys.add(actual_key)
        
        config['binanceAccounts'][str(i)] = {
            'name': actual_name,
            'apiKey': actual_key,
            'apiSecret': args_dict.get(f'BINANCE_API_SECRET_{i}', secret),
            'pair_pattern': pair_pattern  # Pass the pair pattern as is (or None if not provided)
        }
        i += 1

    # Validate configuration
    if not config['krakenAccounts'] and not config['binanceAccounts']:
        raise ValueError("No accounts configured. At least one Kraken or Binance account is required")
    if not config['taxYear']:
        raise ValueError("Tax year must be provided in .env or via --TAX_YEAR")
        
    # Convert dict config to dataclass for Kraken.
    kraken_accounts = {
        account_id: KrakenAccount(
            name=account['name'],
            api_key=account['apiKey'],
            api_secret=account['apiSecret']
        )
        for account_id, account in config['krakenAccounts'].items()
    }
    # Convert dict config to dataclass for Binance.
    binance_accounts = {
        account_id: BinanceAccount(
            name=account['name'],
            api_key=account['apiKey'],
            api_secret=account['apiSecret'],
            pair_pattern=account.get('pair_pattern')
        )
        for account_id, account in config['binanceAccounts'].items()
    }
    
    return Configuration(
        kraken_accounts=kraken_accounts,
        binance_accounts=binance_accounts,  # Added Binance accounts.
        settlement_day=config['settlementDay'],
        tax_year=config['taxYear'],
        previous_year_cost_field36=config['previousYearCostField36']
    )