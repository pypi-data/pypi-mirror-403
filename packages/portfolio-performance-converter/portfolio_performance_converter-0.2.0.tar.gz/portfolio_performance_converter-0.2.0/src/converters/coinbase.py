import re
from typing import Optional

import pandas as pd

from ..utils import setup_logger
from .base import BaseConverter

logger = setup_logger(__name__)

class CoinbaseConverter(BaseConverter):
    @property
    def name(self) -> str:
        return "Coinbase"

    @property
    def instructions(self) -> str:
        return """
        <div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 5px;">
            <p><strong>Step-by-step instructions:</strong></p>
            <ol style="margin-left: 20px;">
                <li>Log in and go to <a href="https://accounts.coinbase.com/statements" target="_blank">Statements / Reports</a>.</li>
                <li>Click <b>Generate Report</b> (Custom Statement).</li>
                <li>Set <b>Format</b> to CSV.</li>
                <li>Select the <b>Date Range</b>.</li>
                <li>Click <b>Generate</b> and then Download.</li>
            </ol>
            <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">
                <i>Note: The file should verify the presence of 'Transaction Type', 'Asset', and 'Quantity Transacted'.</i>
            </p>
        </div>
        """

    @property
    def input_data_types(self) -> list[dict]:
        return [
            {"field_name": "Transaction Type", "field_type": "String", "description": "Type of transaction", "example": "Buy"},
            {"field_name": "Asset", "field_type": "String", "description": "Asset symbol or name", "example": "BTC"},
            {"field_name": "Quantity Transacted", "field_type": "Decimal", "description": "Amount of asset", "example": "0.5"},
            {"field_name": "Price Currency", "field_type": "String", "description": "Currency for the price", "example": "EUR"},
            {"field_name": "Subtotal", "field_type": "Decimal", "description": "Value before fees", "example": "100.00"},
            {"field_name": "Fees and/or Slippage", "field_type": "Decimal", "description": "Fees paid", "example": "1.50"},
            {"field_name": "Total (inclusive of fees)", "field_type": "Decimal", "description": "Total value", "example": "101.50"},
        ]

    def detect(self, input_path: str) -> bool:
        """Check if the file is a Coinbase CSV export."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                # Read first few lines to find signature
                chunk = f.read(4096)
                
            # Coinbase exports usually start with "Transactions" or have specific headers
            # Row with columns: ID,Timestamp,Transaction Type,Asset,Quantity Transacted,Price Currency,...
            
            # Check for header columns presence
            required_cols = ['Transaction Type', 'Asset', 'Quantity Transacted', 'Price Currency']
            if all(col in chunk for col in required_cols):
                return True
                
            return False
        except Exception:
            return False

    def _convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """Convert Coinbase CSV to Portfolio Performance CSV."""
        
        # Find header row
        header_row = 0
        with open(input_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if 'Transaction Type' in line and 'Asset' in line:
                    header_row = i
                    break
        
        # We must use skip_blank_lines=False to ensure line counting matches the enumerate above
        df = pd.read_csv(input_path, header=header_row, skip_blank_lines=False)
        
        # Remove empty rows if any
        df.dropna(how='all', inplace=True)

        
        # Helper to clean currency strings (e.g. "€200.00" -> 200.00)
        def clean_currency(val):
            if isinstance(val, (int, float)):
                return val
            if pd.isna(val) or val == '':
                return 0.0
            # Remove currency symbols and non-numeric chars except period and minus
            # Typically Coinbase uses things like "€200.00" or "$200.00"
            # We want to keep just the number.
            cleaned = re.sub(r'[^\d.-]', '', str(val))
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        # Apply cleaning
        numeric_cols = [
            'Quantity Transacted', 
            'Price at Transaction', 
            'Subtotal', 
            'Total (inclusive of fees and/or spread)', 
            'Fees and/or Spread'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(clean_currency)

        # Parse Date
        # Format: 2025-11-14 10:26:44 UTC
        df['Date'] = pd.to_datetime(df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Map to PP format
        results = []
        
        for _, row in df.iterrows():
            trans_type = row['Transaction Type']
            asset = row['Asset']
            qty = row['Quantity Transacted']
            subtotal = row.get('Subtotal', 0)
            total = row.get('Total (inclusive of fees and/or spread)', 0)
            fees = row.get('Fees and/or Spread', 0)
            notes = row.get('Notes', '')
            # Ensure string in case of NaN
            if pd.isna(notes):
                notes = ''
            
            price_currency = row.get('Price Currency', 'EUR') # Default to EUR if missing
            
            pp_data = {
                'Date': row['Date'],
                'Note': notes
            }

            # Normalize values (ensure positive where expected by PP or logic)
            abs_qty = abs(qty)
            abs_total = abs(total)
            abs_subtotal = abs(subtotal)
            
            # Coinbase uses negative quantity for outgoing, positive for incoming.
            
            if asset.upper() in ['EUR', 'USD', 'GBP', 'USDT', 'USDC']: # Treat as Cash/Fiat if used as currency? 
                # Wait, USDT/USDC are crypto but often treated as cash in some contexts. 
                # But in PP they are usually Securities unless mapped to a Currency Account.
                # 'Price Currency' is usually the Fiat. 
                pass

            is_fiat_asset = asset.upper() in ['EUR', 'USD', 'GBP'] # Extend as needed

            if is_fiat_asset:
                pp_data['Transaction Currency'] = asset
                pp_data['Value'] = abs_subtotal if abs_subtotal > 0 else abs_total # Value should be the amount
                
                if trans_type == 'Deposit':
                    pp_data['Type'] = 'Deposit'
                elif trans_type == 'Withdrawal':
                    pp_data['Type'] = 'Removal'
                else:
                    # E.g. rewards in fiat?
                    pp_data['Type'] = 'Deposit' # Generically
            else:
                # Crypto Asset
                pp_data['Transaction Currency'] = price_currency
                pp_data['Shares'] = abs_qty
                
                # Construct Ticker Symbol: ASSET/CURRENCY
                if price_currency:
                     pp_data['Ticker Symbol'] = f"{asset}/{price_currency}"
                else:
                     pp_data['Ticker Symbol'] = asset
                     
                pp_data['Fees'] = fees
                
                # Value for PP is usually the Total amount in Transaction Currency
                # For Buy: Value is what you paid.
                # For Sell: Value is what you got.
                pp_data['Value'] = abs_subtotal # Excludes fees usually in PP logic depending on Type.
                # Actually, standard PP Import:
                # Buy: Type=Buy, Shares, Value (Amount), Fees.
                # If I pay 200 EUR total, 195.25 is Asset Value, 4.75 Fees.
                # PP logic: Amount = Value + Fees (for Buy). 
                # So if I map Value = 195.25 and Fees = 4.75, Amount will be 200. Correct.
                
                if trans_type == 'Buy':
                    pp_data['Type'] = 'Buy'
                    pp_data['Value'] = abs_subtotal
                elif trans_type == 'Sell':
                    pp_data['Type'] = 'Sell'
                    pp_data['Value'] = abs_subtotal
                elif trans_type == 'Send':
                    pp_data['Type'] = 'Transfer (Outbound)'
                    # For delivery, value is optional or market value. 
                    # Coinbase gives us the value at transaction time in 'Subtotal' or 'Total'.
                    pp_data['Value'] = abs_total # Use total value as proxy for market value
                elif trans_type == 'Receive' or trans_type == 'Deposit':
                    pp_data['Type'] = 'Transfer (Inbound)'
                    pp_data['Value'] = abs_total 
                elif trans_type == 'Convert':
                    # Convert is tricky. usually involves two legs. 
                    # But Coinbase simple CSV often shows it as one rows or two?
                    # If strictly one row: "Converted 0.1 BTC to ETH". 
                    # Need to check sample. Sample doesn't have it.
                    # Assuming it might appear as Buy or Sell or distinct.
                    # Best effort: Treat as Trade.
                    if qty > 0:
                        pp_data['Type'] = 'Buy' # Receiving asset
                    else:
                        pp_data['Type'] = 'Sell' # Sending asset
                    pp_data['Value'] = abs_subtotal
                else:
                    # Fallback
                    pp_data['Type'] = 'Transfer (Inbound)' if qty > 0 else 'Transfer (Outbound)'
                    pp_data['Value'] = abs_total

            results.append(pp_data)

        # Create DataFrame
        out_df = pd.DataFrame(results)
        
        return out_df

