import os

import pytest

from src.converters.xtb import XTBConverter


def test_xtb_conversion_original_currency():
    converter = XTBConverter()
    input_path = 'tests/data/xtb_account.xlsx'
    
    if not os.path.exists(input_path):
        pytest.skip(f"Skipping test, file not found: {input_path}")

    df = converter.convert(input_path)
    
    # Find the GOOGL.US purchase
    # Date: 2025-12-05, Type: Buy
    purchase = df[(df['Type'] == 'Buy') & (df['Ticker Symbol'] == 'GOOGL')]
    
    assert not purchase.empty, "Purchase not found"
    row = purchase.iloc[0]
    
    # Check if currency is USD (original) instead of EUR (account)
    assert row['Transaction Currency'] == 'USD', f"Expected USD, got {row['Transaction Currency']}"
    
    # Check Value. Should be positive
    assert row['Value'] > 0, f"Expected positive Value, got {row['Value']}"
    
    # Check Exchange Rate
    assert row['Exchange Rate'] != '', "Exchange Rate should not be empty"
    # We can't check exact value as data is randomized, but it should be a valid float
    assert float(row['Exchange Rate']) > 0

    # Check Dividend (should remain EUR)
    dividend = df[df['Type'] == 'Dividend']
    if not dividend.empty:
        div_row = dividend.iloc[0]
        assert div_row['Transaction Currency'] == 'EUR', f"Expected EUR for Dividend, got {div_row['Transaction Currency']}"
