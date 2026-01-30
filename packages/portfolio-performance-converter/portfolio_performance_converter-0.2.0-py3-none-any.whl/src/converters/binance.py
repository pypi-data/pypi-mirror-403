from typing import Optional

import pandas as pd

from ..utils import setup_logger
from .base import BaseConverter

logger = setup_logger(__name__)

class BinanceConverter(BaseConverter):
    @property
    def name(self) -> str:
        return "Binance"

    @property
    def instructions(self) -> str:
        return """
        <div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 5px;">
            <p><strong>Step-by-step instructions:</strong></p>
            <ol style="margin-left: 20px;">
                <li>Go to <a href="https://www.binance.com/es/my/wallet/history/overview" target="_blank">Transaction History</a> in your Binance Wallet.</li>
                <li>Click top-right button <b>Export</b> and then <b>Export Transaction Records</b>.</li>
                <li>Select the <b>Time Range</b>, accounts and coins.</li>
                <li>Click <b>Generate</b> and wait.</li>
                <li>Download the zip file in the <b>Export Details</> of the same modal window.</li>
                <li>Unzip the file.</li> 
            </ol>
        </div>
        """

    @property
    def input_data_types(self) -> list[dict]:
        return [
            {"field_name": "User_ID", "field_type": "Integer", "description": "User identifier", "example": "12345678"},
            {"field_name": "UTC_Time", "field_type": "DateTime", "description": "Transaction timestamp in UTC", "example": "2023-01-01 12:00:00"},
            {"field_name": "Account", "field_type": "String", "description": "Account type", "example": "Spot"},
            {"field_name": "Operation", "field_type": "String", "description": "Type of operation", "example": "Buy"},
            {"field_name": "Coin", "field_type": "String", "description": "Asset symbol", "example": "BTC"},
            {"field_name": "Change", "field_type": "Decimal", "description": "Amount changed", "example": "0.001"},
            {"field_name": "Remark", "field_type": "String", "description": "Notes/Remarks", "example": ""},
        ]

    def detect(self, input_path: str) -> bool:
        """Check if the file is a Binance CSV export."""
        try:
            # Try reading the first few lines to check columns
            # Binance Transaction History usually has User_ID, UTC_Time, Account, Operation, Coin, Change, Remark
            df = pd.read_csv(input_path, nrows=5)
            
            required_cols = {'User_ID', 'UTC_Time', 'Operation', 'Coin', 'Change'}
            if required_cols.issubset(df.columns):
                return True
                
            # Alternative format: Trade History
            # Date(UTC), Pair, Side, Price, Executed, Amount, Fee
            trade_cols = {'Date(UTC)', 'Pair', 'Side', 'Price', 'Executed', 'Amount'}
            if trade_cols.issubset(df.columns):
                return True
                
            return False
        except Exception:
            return False

    def _convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """Convert Binance CSV to Portfolio Performance CSV."""
        df = pd.read_csv(input_path)
        
        # Check which format it is
        if 'User_ID' in df.columns and 'Operation' in df.columns:
            return self._convert_transaction_history(df)
        elif 'Date(UTC)' in df.columns and 'Pair' in df.columns:
            return self._convert_trade_history(df)
        else:
            raise ValueError("Unknown Binance CSV format")

    def _convert_transaction_history(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert the 'Transaction History' format. 
        This is a ledger of balance changes. We attempt to reconstruct trades by grouping
        transactions.
        
        Grouping strategy:
        1. If 'Remark' contains a Wallet ID (e.g. 'Via CashBalance - Wallet/...'), use that to group.
        2. Otherwise, group by time (within close proximity).
        """
        output = []
        
        # Ensure UTC_Time is datetime
        df['UTC_Time'] = pd.to_datetime(df['UTC_Time'])
        
        # Sort by time to make processing easier
        df = df.sort_values('UTC_Time')
        
        # Define Known Fiats/Stables to identify the "Currency" side of a trade
        FIAT_STABLE = {'EUR', 'USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'GBP', 'AUD', 'CAD', 'CHF', 'JPY'}
        
        # Create a grouping key
        df['Group_ID'] = df.apply(self._get_group_id, axis=1)
        
        # Now iterate over groups
        for _group_id, group in df.groupby('Group_ID'):
            # Timestamp for the group - verify if they are close enough
            # If grouped by Remark, time can be slightly different (e.g. 5s apart).
            # We take the max time as the date.
            timestamp = group['UTC_Time'].max()
            date_str = timestamp.strftime('%Y-%m-%d')
            
            # Categories
            pos_changes = group[group['Change'] > 0]
            neg_changes = group[group['Change'] < 0]
            
            # Check for Trade characteristic keywords
            trade_keywords = ['Transaction Related', 'Small Assets Exchange BNB', 'Buy Crypto With Fiat', 'Sell Crypto To Fiat', 'Buy', 'Sell']
            ops = group['Operation'].unique()
            is_trade_related = any(k in op for op in ops for k in trade_keywords)
            
            if is_trade_related and not pos_changes.empty and not neg_changes.empty:
                 # Attempt to reconstruct trade
                if len(pos_changes) == 1 and len(neg_changes) >= 1:
                    incoming = pos_changes.iloc[0]
                    
                    # Find outgoing (main cost)
                    outgoing_candidates = neg_changes[neg_changes['Coin'] != incoming['Coin']]
                    
                    if not outgoing_candidates.empty:
                        # Largest absolute value is likely the cost
                        outgoing = outgoing_candidates.loc[outgoing_candidates['Change'].abs().idxmax()]
                        
                        # Any other negatives are fees
                        fee_rows = group[
                            (group.index != incoming.name) & 
                            (group.index != outgoing.name) &
                            (group['Change'] < 0)
                        ]
                        fee_value = fee_rows['Change'].abs().sum() if not fee_rows.empty else 0.0
                        
                        in_coin = incoming['Coin']
                        out_coin = outgoing['Coin']
                        
                        # Determine Type
                        if out_coin in FIAT_STABLE and in_coin not in FIAT_STABLE:
                             # BUY Crypto with Fiat
                            output.append({
                                'Date': date_str,
                                'Type': 'Buy',
                                'Shares': incoming['Change'],
                                'Value': abs(outgoing['Change']),
                                'Transaction Currency': out_coin,
                                'Ticker Symbol': f"{in_coin}/{out_coin}",
                                'Fees': fee_value,
                                'Note': f"Trade: {incoming['Operation']} ({in_coin}/{out_coin})"
                            })
                            continue
                        elif in_coin in FIAT_STABLE and out_coin not in FIAT_STABLE:
                            # SELL Crypto for Fiat
                            output.append({
                                'Date': date_str,
                                'Type': 'Sell',
                                'Shares': abs(outgoing['Change']),
                                'Value': incoming['Change'],
                                'Transaction Currency': in_coin,
                                'Ticker Symbol': f"{out_coin}/{in_coin}",
                                'Fees': fee_value,
                                'Note': f"Trade: {incoming['Operation']} ({out_coin}/{in_coin})"
                            })
                            continue
                        else:
                            # Crypto-Crypto
                            output.append({
                                'Date': date_str,
                                'Type': 'Buy',
                                'Shares': incoming['Change'],
                                'Value': abs(outgoing['Change']),
                                'Transaction Currency': out_coin,
                                'Ticker Symbol': f"{in_coin}/{out_coin}",
                                'Fees': fee_value,
                                'Note': f"Swap: {incoming['Operation']} ({in_coin}/{out_coin})"
                            })
                            continue
            
            # Fallback: Treat as standalone deposits/removals
            for _index, row in group.iterrows():
                op = row['Operation']
                amount = float(row['Change'])
                coin = row['Coin']
                
                pp_type = 'Deposit' if amount > 0 else 'Removal'
                
                # Check specifics
                if op in ['Deposit', 'Distribution', 'Savings Interest', 'POS Savings Interest']:
                    pp_type = 'Deposit'
                elif op in ['Withdraw']:
                    pp_type = 'Removal'
                
                output.append({
                    'Date': date_str,
                    'Type': pp_type,
                    'Value': abs(amount),
                    'Transaction Currency': coin,
                    'Note': f"Binance - {op} - {row['Remark']}",
                    'Shares': 0,
                    'Fees': 0,
                    'Taxes': 0
                })
        
        return pd.DataFrame(output)

    def _get_group_id(self, row) -> str:
        """
        Generates a grouping ID for transactions.
        """
        remark = str(row['Remark']) if not pd.isna(row['Remark']) else ""
        if 'Via CashBalance - Wallet/' in remark:
            # Group by remark and a small time window (e.g. 1 minute)
            # to avoid grouping independent trades that happen days apart
            # but share the same Wallet ID tag.
            time_bucket = row['UTC_Time'].floor('1min')
            return f"{remark}_{time_bucket}"
        # Fallback to timestamp string for non-linked items
        return f"TIME_{row['UTC_Time']}"

    def _convert_trade_history(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert the 'Trade History' format.
        Columns: Date(UTC), Pair, Side, Price, Executed, Amount, Fee
        """
        output = []
        
        # Ensure Date(UTC) is datetime
        df['Date(UTC)'] = pd.to_datetime(df['Date(UTC)'])
        
        for _index, row in df.iterrows():
            date = row['Date(UTC)'].strftime('%Y-%m-%d')
            pair = row['Pair'] # e.g. BTCUSDT
            side = row['Side'] # BUY or SELL
            price = float(row['Price'])
            executed = float(row['Executed']) # Quantity of base asset
            amount = float(row['Amount']) # Total value in quote asset
            fee = float(row['Fee'].split(' ')[0]) if isinstance(row['Fee'], str) else 0.0 # Fee often has currency
            fee_currency = row['Fee'].split(' ')[1] if isinstance(row['Fee'], str) and ' ' in row['Fee'] else ''
            
            # Determine Base and Quote currency
            # This is tricky generically, but usually Quote is USDT, EUR, BTC, ETH, BNB
            # We assume Pair ends with Quote.
            # Common quotes: USDT, USDC, BUSD, EUR, USD, BTC, ETH, BNB
            known_quotes = ['USDT', 'USDC', 'BUSD', 'EUR', 'USD', 'BTC', 'ETH', 'BNB', 'DAI']
            quote = next((q for q in known_quotes if pair.endswith(q)), None)
            
            if quote:
                base = pair[:-len(quote)]
            else:
                # Fallback, maybe look at Price? 
                # If we can't guess, we might fail or prompt. 
                # Let's default to parsing matching simple logic or leave it blank
                base = pair # fallback
                quote = "?"

            pp_type = 'Buy' if side.upper() == 'BUY' else 'Sell'
            
            # For PP:
            # Buy: Value = amount (cost), Shares = executed (qty)
            # Sell: Value = amount (proceeds), Shares = executed (qty)
            
            record = {
                'Date': date,
                'Type': pp_type,
                'Value': amount,
                'Transaction Currency': quote,
                'Shares': executed,
                'Fees': fee, # Note: Fee currency might differ from transaction currency! PP allows Fee in separate currency? No, usually same. 
                             # If fee is in different currency (e.g. BNB), this is complex for CSV import.
                             # We'll just put the number and Note it if currency mismatches.
                'Taxes': 0,
                'Ticker Symbol': f"{base}/{quote}",
                'Security Name': base,
                'Note': f"Binance - Trade {pair} at {price}. Fee: {fee} {fee_currency}"
            }
            output.append(record)
            
        return pd.DataFrame(output)
