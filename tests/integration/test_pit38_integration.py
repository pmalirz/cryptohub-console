import os
from decimal import Decimal
from pathlib import Path
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from cryptohub.config import Configuration
from cryptohub.addin_taxpl import process_pit38_tax, load_trades_from_excel

def setup_test_config():
    """Create a test configuration."""
    return Configuration(
        kraken_accounts={},
        binance_accounts={},
        settlement_day=-1,
        tax_year=2024,
        previous_year_cost_field36=Decimal("0.00")
    )

@patch('cryptohub.addin_taxpl.questionary')
def test_pit38_tax_calculation(mock_questionary, tmp_path):
    """Integration test for PIT-38 tax calculation process."""
    # Setup mock responses for text inputs
    mock_text = MagicMock()
    mock_text.ask.side_effect = ["2024", "-1", "0.00"]
    mock_questionary.text.return_value = mock_text

    # Setup mock response for select input
    mock_select = MagicMock()
    mock_select.ask.return_value = "trades.xlsx (default)"
    mock_questionary.select.return_value = mock_select
    
    # Setup
    test_data_path = Path(__file__).parent / "test_data"
    input_file = test_data_path / "trades.xlsx"
    
    # Copy test file to working directory if it doesn't exist
    if not input_file.exists():
        raise FileNotFoundError(f"Test data file not found: {input_file}")
    
    if not Path("trades.xlsx").exists():
        import shutil
        shutil.copy2(input_file, "trades.xlsx")
    
    config = setup_test_config()
    
    # Expected values based on the test data
    expected_values = {
        "year": 2024,
        "field34_income": Decimal("21.52"),
        "field35_costs_current_year": Decimal("0.00"),
        "field36_costs_previous_years": Decimal("0.00"),
        "field37_tax_base": Decimal("21.52"),
        "field38_loss": Decimal("0.00"),
        "field39_tax": Decimal("4.09")  # 19% of 50000
    }
    
    # Process tax calculation
    result = process_pit38_tax(config)
    
    # Verify calculations
    for field, expected in expected_values.items():
        actual = getattr(result, field)
        assert actual == expected, f"Field {field} mismatch: expected {expected}, got {actual}"
    
    # Verify mock calls
    assert mock_questionary.text.call_count == 3, "Expected 3 text prompts"
    assert mock_questionary.select.call_count == 1, "Expected 1 select prompt"