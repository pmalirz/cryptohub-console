import os
from dotenv import load_dotenv
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--krakenKey", type=str, help="Kraken API Key")
    parser.add_argument("--krakenSecret", type=str, help="Kraken API Secret")
    parser.add_argument("--settlementDay", type=int, help="Settlement day for tax calculation (T - 0,1,2,3,...). Default is -1 (Polish regulations).", default=-1)
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    kraken_key = args.krakenKey or os.getenv("KRAKEN_API_KEY", "")
    kraken_secret = args.krakenSecret or os.getenv("KRAKEN_API_SECRET", "")
    settlement_day = args.settlementDay or os.getenv("SETTLEMENT_DAY", "")

    if not kraken_key or not kraken_secret:
        logger.warning("API credentials are missing. Please provide them in .env file or via CLI arguments.")
    else:
        logger.debug("API credentials loaded successfully.")

    return {
        "krakenKey": kraken_key,
        "krakenSecret": kraken_secret,
        "settlementDay": settlement_day
    }