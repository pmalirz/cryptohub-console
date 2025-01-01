# Crypto Tax PL CLI

A command-line tool for Polish crypto traders to:
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

- Python 3.11 or higher
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

```sh
python main.py --krakenKey YOUR_KEY --krakenSecret YOUR_SECRET
```

## Build Executable

```sh
pip install pyinstaller
pyinstaller --onefile main.py
```

## Development

To deactivate the virtual environment when you're done:

```sh
deactivate
```
