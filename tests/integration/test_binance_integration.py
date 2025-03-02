import os
import pytest
import time
from cryptohub.binance import BinanceAPI

# Skip all tests in this file if SKIP_BINANCE_TESTS is set
pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_BINANCE_TESTS") == "1", 
    reason="Binance integration tests disabled via SKIP_BINANCE_TESTS env var"
)


@pytest.fixture
def binance_api():
    key = os.getenv("BINANCE_API_KEY_1", "")
    secret = os.getenv("BINANCE_API_SECRET_1", "")
    pair_pattern = "^SOLEUR$"  # Remember that this require the pair to be exactly SOLEUR on the Binance exchange (this is set up via env / GitHub Actions).
    
    # Skip individual tests if credentials are missing
    if not key or not secret:
        pytest.skip("Binance API credentials not provided")
        
    return BinanceAPI(key, secret, pair_pattern=pair_pattern)


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
            assert txn.trade_id, "Transaction trade_id should not be empty."
            # The volume should be positive.
            assert txn.volume > 0, "Transaction volume should be positive."


def test_download_all_trades_timing(binance_api):
    start_time = time.time()
    transactions = binance_api.download_all_trades()
    end_time = time.time()
    
    execution_time = end_time - start_time
    print(f"\nDownload trades execution time: {execution_time:.2f} seconds")
    
    assert transactions, "Expected non-empty list of transactions"
    assert execution_time < 30, "Download should complete within 30 seconds"

