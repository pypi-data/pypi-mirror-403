import pytest

from src.converters.binance import BinanceConverter


@pytest.fixture
def binance_converter():
    return BinanceConverter()

def test_detect_transaction_history(binance_converter, tmp_path):
    csv_content = """User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
12345,2023-01-01 12:00:00,Spot,Buy,BTC,0.1,
12345,2023-01-01 12:00:00,Spot,Transaction Related,USDT,-2000,
"""
    f = tmp_path / "binance_trans.csv"
    f.write_text(csv_content)
    
    assert binance_converter.detect(str(f)) is True

def test_detect_trade_history(binance_converter, tmp_path):
    csv_content = """Date(UTC),Pair,Side,Price,Executed,Amount,Fee
2023-01-01 12:00:00,BTCUSDT,BUY,20000,0.1,2000,1 USDT
"""
    f = tmp_path / "binance_trades.csv"
    f.write_text(csv_content)
    
    assert binance_converter.detect(str(f)) is True

def test_convert_trade_history(binance_converter, tmp_path):
    csv_content = """Date(UTC),Pair,Side,Price,Executed,Amount,Fee
2023-01-01 12:00:00,BTCUSDT,BUY,20000,0.5,10000,5 USDT
2023-01-02 14:30:00,ETHBUSD,SELL,1500,2,3000,0.001 BNB
"""
    f = tmp_path / "binance_trades.csv"
    f.write_text(csv_content)
    
    df = binance_converter.convert(str(f))
    
    assert len(df) == 2
    # Check first row (Buy)
    row1 = df.iloc[0]
    assert row1['Date'] == '2023-01-01'
    assert row1['Type'] == 'Buy'
    assert row1['Value'] == 10000.0
    assert row1['Transaction Currency'] == 'USDT'
    assert row1['Shares'] == 0.5
    assert row1['Ticker Symbol'] == 'BTC/USDT'
    assert row1['Fees'] == 5.0
    
    # Check second row (Sell)
    row2 = df.iloc[1]
    assert row2['Date'] == '2023-01-02'
    assert row2['Type'] == 'Sell'
    assert row2['Value'] == 3000.0
    assert row2['Transaction Currency'] == 'BUSD'
    assert row2['Shares'] == 2.0
    assert row2['Ticker Symbol'] == 'ETH/BUSD' 
    # Fee is 0.001 but in BNB, our logic extracts the number.
    assert row2['Fees'] == 0.001

def test_convert_transaction_history_simple(binance_converter, tmp_path):
    # This tests the basic ledger logic which just does Deposits/Removals for now
    csv_content = """User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
1,2023-01-01 10:00,Spot,Deposit,USDT,1000,
1,2023-01-02 11:00,Spot,Withdraw,BTC,-0.5,
"""
    f = tmp_path / "binance_trans.csv"
    f.write_text(csv_content)
    
    df = binance_converter.convert(str(f))
    
    assert len(df) == 2
    
    row1 = df.iloc[0]
    assert row1['Type'] == 'Deposit'
    assert row1['Value'] == 1000.0
    assert row1['Transaction Currency'] == 'USDT'
    
    row2 = df.iloc[1]
    assert row2['Type'] == 'Removal'
    assert row2['Value'] == 0.5
    assert row2['Transaction Currency'] == 'BTC'

def test_convert_transaction_history_reconstruct_buy(binance_converter, tmp_path):
    # Test pairing: Buy BTC with USDT
    # Ledger: -20000 USDT, +1 BTC, same time
    csv_content = """User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
1,2023-01-01 12:00:00,Spot,Transaction Related,USDT,-20000,
1,2023-01-01 12:00:00,Spot,Transaction Related,BTC,1,
"""
    f = tmp_path / "binance_trans_buy.csv"
    f.write_text(csv_content)
    
    df = binance_converter.convert(str(f))
    
    assert len(df) == 1
    row = df.iloc[0]
    assert row['Type'] == 'Buy'
    assert row['Ticker Symbol'] == 'BTC/USDT'
    assert row['Shares'] == 1.0
    assert row['Transaction Currency'] == 'USDT'
    assert row['Value'] == 20000.0

def test_convert_transaction_history_reconstruct_sell(binance_converter, tmp_path):
    # Test pairing: Sell ETH for BUSD with Fee in BNB
    # Ledger: -2 ETH, +3000 BUSD, -0.01 BNB (fee)
    csv_content = """User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
1,2023-01-02 14:00:00,Spot,Transaction Related,ETH,-2,
1,2023-01-02 14:00:00,Spot,Transaction Related,BUSD,3000,
1,2023-01-02 14:00:00,Spot,Transaction Related,BNB,-0.01,
"""
    f = tmp_path / "binance_trans_sell.csv"
    f.write_text(csv_content)
    
    df = binance_converter.convert(str(f))
    
    assert len(df) == 1
    row = df.iloc[0]
    assert row['Type'] == 'Sell'
    assert row['Ticker Symbol'] == 'ETH/BUSD'
    assert row['Shares'] == 2.0
    assert row['Transaction Currency'] == 'BUSD'
    assert row['Value'] == 3000.0
    # Fee logic: sum of other negatives
    assert row['Fees'] == 0.01

def test_convert_transaction_history_linked_trades_real_example(binance_converter, tmp_path):
    # Test based on real file: rows linked by Remark but with different timestamps
    csv_content = """User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
1,2025-11-15 21:30:35,Spot,Buy Crypto With Fiat,EUR,-400.00,"Via CashBalance - Wallet/WALLET_ID_123"
1,2025-11-15 21:30:40,Spot,Buy Crypto With Fiat,BTC,0.00486539,"Via CashBalance - Wallet/WALLET_ID_123"
1,2025-11-21 08:19:45,Spot,Buy Crypto With Fiat,EUR,-400.00,"Via CashBalance - Wallet/WALLET_ID_124"
1,2025-11-21 08:19:50,Spot,Buy Crypto With Fiat,BTC,0.00546378,"Via CashBalance - Wallet/WALLET_ID_124"
"""
    f = tmp_path / "binance_real_partial.csv"
    f.write_text(csv_content)
    
    df = binance_converter.convert(str(f))
    
    assert len(df) == 2
    
    # Trade 1
    t1 = df.iloc[0]
    assert t1['Date'] == '2025-11-15'
    assert t1['Type'] == 'Buy'
    assert t1['Ticker Symbol'] == 'BTC/EUR'
    assert t1['Shares'] == 0.00486539
    assert t1['Value'] == 400.0
    assert t1['Transaction Currency'] == 'EUR'
    
    # Trade 2
    t2 = df.iloc[1]
    assert t2['Date'] == '2025-11-21'
    assert t2['Type'] == 'Buy'
    assert t2['Ticker Symbol'] == 'BTC/EUR'
    assert t2['Shares'] == 0.00546378
    assert t2['Value'] == 400.0

def test_convert_binance_sample_file(binance_converter):
    input_file = 'tests/data/binance_sample.csv'
    df = binance_converter.convert(input_file)
    
    assert df is not None
    assert len(df) > 0
    
    # Check for the Deposits
    deposits = df[df['Type'] == 'Deposit']
    assert len(deposits) >= 3
    
    # Check for the Buys reconstructed
    buys = df[df['Type'] == 'Buy']
    assert len(buys) == 2
    assert all(buys['Ticker Symbol'] == 'BTC/EUR')



