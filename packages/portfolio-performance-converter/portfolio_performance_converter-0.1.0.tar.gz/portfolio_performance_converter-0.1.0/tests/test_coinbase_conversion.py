import os

import pytest

from src.converters.coinbase import CoinbaseConverter


class TestCoinbaseConverter:
    @pytest.fixture
    def converter(self):
        return CoinbaseConverter()

    @pytest.fixture
    def sample_file(self):
        # Using the anonymized sample file in tests/data
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, 'data', 'coinbase_sample.csv')

    def test_detect(self, converter, sample_file):
        assert converter.detect(sample_file) is True

    def test_convert(self, converter, sample_file):
        df = converter.convert(sample_file)
        
        # Verify columns
        # Note: Depending on implementation, not all cols might be present if empty, but let's check basic ones
        assert 'Date' in df.columns
        assert 'Type' in df.columns
        assert 'Value' in df.columns
        
        # Check a specific row - Buy BTC
        # 2025-11-04 22:45:33 UTC -> Buy 0.00221328 BTC for 200 EUR (195.25 subtotal + 4.74 fees)
        buy_row = df[(df['Date'] == '2025-11-04 22:45:33') & (df['Type'] == 'Buy')]
        assert not buy_row.empty
        row = buy_row.iloc[0]
        assert row['Ticker Symbol'] == 'BTC/EUR'
        assert abs(row['Shares'] - 0.00221328) < 0.0000001
        assert str(row['Note']).startswith('Coinbase - ')
        assert 'Bought 0.00221328 BTC' in str(row['Note'])
        assert abs(row['Value'] - 195.25721) < 0.01
        assert abs(row['Fees'] - 4.742794) < 0.01
        assert row['Transaction Currency'] == 'EUR'

    def test_convert_send(self, converter, sample_file):
        df = converter.convert(sample_file)
        
        # Check Send BTC
        # 6902782c05bd562a52375bbe... Send -0.00321849 BTC
        send_row = df[df['Date'] == '2025-10-29 20:25:16']
        assert not send_row.empty
        row = send_row.iloc[0]
        assert row['Type'] == 'Transfer (Outbound)'
        assert row['Ticker Symbol'] == 'BTC/EUR'
        assert abs(row['Shares'] - 0.00321849) < 0.0000001

    def test_convert_fiat_deposit(self, converter, sample_file):
        df = converter.convert(sample_file)
        
        # Check Deposit EUR
        # 690a81a952165b8341a99aa2... Deposit 200 EUR
        dep_row = df[df['Date'] == '2025-11-04 22:43:53']
        assert not dep_row.empty
        row = dep_row.iloc[0]
        assert row['Type'] == 'Deposit'
        assert row['Transaction Currency'] == 'EUR'
        assert abs(row['Value'] - 200.0) < 0.01
