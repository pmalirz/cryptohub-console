import os
import pytest
import time
from cryptohub.binance import BinanceAPI
from cryptohub.config import load_config

@pytest.fixture
def binance_api():
    #config = load_config()["binance"][0]
    key = ""
    secret = ""
    return BinanceAPI(key, secret)

def test_download_asset_pairs_integration(binance_api):
    pairs = binance_api.download_asset_pairs()
    
    # Verify that some pairs are returned.
    assert pairs, "Expected non-empty pair mapping from Binance exchange info."
    
    # Verify that the mapping contains the SOLEUR pair.
    # Note: Adjust the key as needed if your desired pair name is different.
    assert "SOLEUR" in pairs, "Expected to find the SOLEUR pair in the exchange info."

def test_download_all_orders_integration(binance_api):
    transactions = binance_api.download_all_trades()
    
    # Verify the returned data is a list.
    assert isinstance(transactions, list), "Expected transactions to be a list."
    
    assert transactions, "Expected non-empty list of transactions."
    
    # If any transactions are returned, check that each has essential fields.
    if transactions:
        for txn in transactions:
            assert txn.ordertxid, "Transaction ordertxid should not be empty."
            # The volume should be positive.
            assert txn.vol > 0, "Transaction volume should be positive."

def test_download_all_trades_timing(binance_api):
    start_time = time.time()
    transactions = binance_api.download_all_trades()
    end_time = time.time()
    
    execution_time = end_time - start_time
    print(f"\nDownload trades execution time: {execution_time:.2f} seconds")
    
    assert transactions, "Expected non-empty list of transactions"
    assert execution_time < 30, "Download should complete within 30 seconds"

