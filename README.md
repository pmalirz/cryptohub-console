# CryptoHub CLI

A command-line tool for crypto traders to:

- Download trading history from Kraken exchange
- Fetch NBP (National Bank of Poland) exchange rates
- Calculate tax-relevant transaction data
- Export results to JSON and CSV formats

## Features

- 🔄 Automatic trade history download from Kraken API
- 💱 NBP exchange rate integration
- 📊 Export to JSON and CSV formats
- 🔒 Secure API key handling

## Requirements

- Python 3.11
- Kraken API credentials
- Internet connection for Kraken and NBP data

### Managing Python with Scoop

Check your Python installation and versions:

```powershell
# Check current Python path
scoop which python

# List installed Python versions (Method 1)
Get-ChildItem -Path $env:SCOOP\apps\python* -Directory

# List installed Python versions (Method 2)
scoop info python

# Check Python version
python --version
```

## Setup

### Virtual Environment

You can create a virtual environment using your default Python or specify a particular version:

```sh
# Using default Python version
python -m venv venv

# Using specific Python version from Scoop
$env:SCOOP\apps\python\3.11.3\python.exe -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate

# On Linux/macOS
# source venv/bin/activate
```

### Install Dependencies

With the virtual environment activated, install the required packages:

```sh
pip install -r requirements.txt
```

## Usage

You can run the project as a module from the project root:

```sh
python -m cryptohub.main --KRAKEN_API_KEY_1 YOUR_KEY --KRAKEN_API_SECRET_1 YOUR_SECRET
```

Alternatively, if you wish to run an executable after building it, refer to the build instructions below.

## Configuration

### Environment Variables

A `.env` file is the preferred way to setup the CryptHub (comparing to passing the parameters via commandline parameters as stated above).
Create the `.env` file in the project root directory with your configuration:

```properties
# Kraken account configuration
KRAKEN_1=My Account Name              # Optional account name
KRAKEN_API_KEY_1=your_api_key         # Required API key
KRAKEN_API_SECRET_1=your_api_secret   # Required API secret

# You can configure multiple Kraken accounts by incrementing the number:
KRAKEN_2=Second Account
KRAKEN_API_KEY_2=second_api_key
KRAKEN_API_SECRET_2=second_api_secret

# Binance account configuration
BINANCE_1=My Binance Account          # Optional account name
BINANCE_API_KEY_1=your_binance_api_key         # Required API key
BINANCE_API_SECRET_1=your_binance_api_secret   # Required API secret
# Optional regex filtering of trading pairs, e.g., to include only pairs ending with USDT or EUR.
BINANCE_PAIR_PATTERN_1=.*(USDT|EUR)$

# Tax calculation settings
SETTLEMENT_DAY=-1                     # Settlement day for tax calculations
TAX_YEAR=2024                         # Required tax year

# Tax PL Config - Cost moved from the previous year (default: 0.00)
PREVIOUS_YEAR_COST_FIELD36=0

# Filtering trades based on quote asset:
# Provide a comma separated list of quote assets (e.g., EUR,USD).
# If empty, no filtering will be applied.
FILTER_QUOTE_ASSETS=EUR,USD
```

### Command Line Arguments

All environment variables can be overridden using command line arguments:

```sh
# Override tax year and settlement day
python -m cryptohub.main --TAX_YEAR 2024 --SETTLEMENT_DAY -1

# Override Kraken API credentials
python -m cryptohub.main --KRAKEN_1 "My Account" --KRAKEN_API_KEY_1 your_key --KRAKEN_API_SECRET_1 your_secret
```

### Configuration Priority

1. Command line arguments take precedence over environment variables  
2. Environment variables from `.env` file are used as defaults  
3. If neither is provided, default values are used where possible

### Required Parameters

- `TAX_YEAR`: Must be provided either in `.env` or via command line  
- At least one Kraken account must be configured with API key and secret

## Build Executable

To build the executable (named `cryptohub.exe`), install PyInstaller and run the following command with your modified spec file:

```sh
pyinstaller main.spec
```

## Development

To deactivate the virtual environment when you're done:

```sh
deactivate
```
