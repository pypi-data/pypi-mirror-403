import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

import pandas as pd

from ..market_data import convert_xtb_suffix, get_symbol_info
from ..utils import load_config, setup_logger
from .base import BaseConverter

logger = setup_logger(__name__)

class XTBConverter(BaseConverter):
    @property
    def name(self) -> str:
        return "XTB"

    @property
    def instructions(self) -> str:
        return """
        <div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 5px;">
            <p><strong>Step-by-step instructions:</strong></p>
            <ol style="margin-left: 20px;">
                <li>Open <a href="https://xstation5.xtb.com/" target="_blank">xStation 5</a>.</li>
                <li>Navigate to the <b>General view</b> tab in the left panel.</li>
                <li>Click in the <b>History</b> card</li>
                <li>Select the <b>Cash Operations</b> tab within the history view.</li>
                <li>Click the <b>Export</b> button.</li>
                <li>Choose <b>Export to Excel</b>.</li>
                <li>Ensure the file contains the sheet named <b>'CASH OPERATION HISTORY'</b>.</li>
            </ol>
        </div>
        """

    @property
    def input_data_types(self) -> list[dict]:
        return [
            {"field_name": "ID", "field_type": "Integer", "description": "Transaction ID", "example": "123456"},
            {"field_name": "Type", "field_type": "String", "description": "Type of operation (Deposit, Profit, etc.)", "example": "Stocks/ETF purchase"},
            {"field_name": "Time", "field_type": "DateTime", "description": "Timestamp", "example": "01.01.2023 12:00:00"},
            {"field_name": "Symbol", "field_type": "String", "description": "Asset symbol", "example": "AAPL.US"},
            {"field_name": "Comment", "field_type": "String", "description": "Notes", "example": "OPEN BUY ..."},
            {"field_name": "Amount", "field_type": "Decimal", "description": "Value change", "example": "-1000.00"},
        ]

    def detect(self, input_path: str) -> bool:
        """Check if the file is an XTB Excel export."""
        try:
            # XTB exports are Excel files with a specific sheet name
            xl = pd.ExcelFile(input_path)
            return 'CASH OPERATION HISTORY' in xl.sheet_names
        except Exception:
            return False

    def _convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """Convert XTB Excel to Portfolio Performance CSV."""
        return convert_xtb(
            input_path, 
            config_path=config_path,
            cash_account='',
            securities_account=''
        )

def parse_shares_from_comment(comment: str) -> float:
    """Extract number of shares from comment like 'OPEN BUY 1 @ 321.87'."""
    if not isinstance(comment, str):
        return 0.0
    
    # Match "OPEN BUY <shares> @" or "OPEN SELL <shares> @"
    m = re.search(r"OPEN (?:BUY|SELL) ([\d\.]+) @", comment)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return 0.0
    
    # Match "CLOSE BUY <shares> @" or "CLOSE SELL <shares> @" (if they appear in Cash Ops)
    m = re.search(r"CLOSE (?:BUY|SELL) ([\d\.]+) @", comment)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return 0.0
            
    return 0.0

def _load_sheet_flexible(input_path: str, sheet_name: str, key_column: str) -> pd.DataFrame:
    """Load a sheet by searching for the header row."""
    try:
        # Read first 20 rows
        df_preview = pd.read_excel(input_path, sheet_name=sheet_name, header=None, nrows=20)
        
        header_row = -1
        for i, row in df_preview.iterrows():
            # Check if key_column is in the row values (converted to string)
            row_vals = [str(v).strip() for v in row.values]
            if key_column in row_vals:
                header_row = cast(int, i)
                break
        
        if header_row != -1:
            return pd.read_excel(input_path, sheet_name=sheet_name, header=header_row)
    except Exception as e:
        logger.warning(f"Could not load sheet {sheet_name}: {e}")
    
    return pd.DataFrame()

def _load_positions(input_path: str) -> List[Dict[str, Any]]:
    """Load Open and Closed positions into a unified list."""
    positions = []
    try:
        xl = pd.ExcelFile(input_path)
        sheet_names = xl.sheet_names
        
        # Load OPEN POSITION sheets
        for sheet in sheet_names:
            if isinstance(sheet, str) and sheet.startswith('OPEN POSITION'):
                df = _load_sheet_flexible(input_path, sheet, 'Position')
                if not df.empty:
                    for _, row in df.iterrows():
                        positions.append({
                            'symbol': str(row.get('Symbol', '')).strip(),
                            'open_time': row.get('Open time'),
                            'open_price': row.get('Open price'),
                            'volume': row.get('Volume'),
                            'type': 'OPEN'
                        })
                        
        # Load CLOSED POSITION sheets
        if 'CLOSED POSITION HISTORY' in sheet_names:
            df = _load_sheet_flexible(input_path, 'CLOSED POSITION HISTORY', 'Position')
            if not df.empty:
                for _, row in df.iterrows():
                    positions.append({
                        'symbol': str(row.get('Symbol', '')).strip(),
                        'open_time': row.get('Open time'),
                        'open_price': row.get('Open price'),
                        'close_time': row.get('Close time'),
                        'close_price': row.get('Close price'),
                        'volume': row.get('Volume'),
                        'type': 'CLOSED'
                    })
                    
    except Exception as e:
        logger.error(f"Error loading positions: {e}")
        
    return positions

def _find_position_match(
    positions: List[Dict[str, Any]], 
    symbol: str, 
    time_val: datetime, 
    is_open: bool
) -> Optional[Dict[str, Any]]:
    """Find a matching position for a transaction."""
    if not isinstance(time_val, datetime):
        return None
        
    best_match = None
    min_diff = timedelta(seconds=2) # Tolerance
    
    for pos in positions:
        if pos['symbol'] != symbol:
            continue
            
        pos_time = None
        if is_open:
            pos_time = pos.get('open_time')
        else:
            # For close, we look at close_time if available (CLOSED positions)
            # OPEN positions don't have close_time
            if pos['type'] == 'CLOSED':
                pos_time = pos.get('close_time')
            else:
                continue
                
        if not isinstance(pos_time, datetime):
            continue
            
        diff = abs(pos_time - time_val)
        if diff < min_diff:
            min_diff = diff
            best_match = pos
            
    return best_match

def convert_xtb(
    input_path: str, 
    config_path: Optional[str] = None, 
    cash_account: str = '', 
    securities_account: str = ''
) -> pd.DataFrame:
    """Convert XTB Excel to Portfolio Performance CSV."""
    
    logger.info(f"Reading file: {input_path}")
    
    # Load positions for currency lookup
    positions = _load_positions(input_path)
    logger.info(f"Loaded {len(positions)} positions for lookup")
    
    # Read Excel - CASH OPERATION HISTORY
    # Header is usually at row 10 (index 10, line 11)
    try:
        df = pd.read_excel(input_path, sheet_name='CASH OPERATION HISTORY', header=10)
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return pd.DataFrame()

    # Filter out empty rows or summary rows
    if 'Type' not in df.columns:
        logger.error("Column 'Type' not found in CASH OPERATION HISTORY")
        return pd.DataFrame()
        
    df = df.dropna(subset=['Type'])
    
    # Load config
    config = load_config(config_path)
    overrides = config.get('overrides', {})
    
    # Prepare output list
    output_rows = []
    
    # Cache for symbol lookups
    symbol_cache: dict[str, dict[str, str]] = {}
    
    for _, row in df.iterrows():
        xtb_type = str(row['Type']).strip()
        xtb_symbol = str(row['Symbol']).strip() if pd.notna(row['Symbol']) else ''
        amount = float(row['Amount']) if pd.notna(row['Amount']) else 0.0
        comment = str(row['Comment']) if pd.notna(row['Comment']) else ''
        time_val = row['Time']
        
        # Parse Date
        if isinstance(time_val, str):
            try:
                dt = datetime.strptime(time_val, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    dt = datetime.strptime(time_val, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    dt = datetime.now() # Fallback
        elif isinstance(time_val, datetime):
            dt = time_val
        else:
            dt = datetime.now()
            
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H:%M:%S')
        
        # Map Transaction Type
        pp_type = ''
        shares = 0.0
        
        if xtb_type == 'deposit':
            pp_type = 'Deposit'
        elif xtb_type == 'withdrawal':
            pp_type = 'Removal'
        elif xtb_type == 'Stock purchase':
            pp_type = 'Buy'
            shares = parse_shares_from_comment(comment)
        elif xtb_type == 'Stock sale': # Guessing the name
            pp_type = 'Sell'
            shares = parse_shares_from_comment(comment)
        elif xtb_type == 'DIVIDENT':
            pp_type = 'Dividend'
        elif xtb_type == 'Withholding Tax':
            pp_type = 'Taxes'
        else:
            # Skip unknown types or handle as Note?
            continue
            
        # Lookup Symbol Info
        yahoo_symbol = ''
        name = ''
        currency = '' # Security currency
        
        if xtb_symbol and xtb_symbol != 'nan':
            # Check overrides
            if xtb_symbol in overrides:
                ov = overrides[xtb_symbol]
                yahoo_symbol = ov.get('symbol', '')
                name = ov.get('name', '')
                currency = ov.get('currency', '')
            
            # If missing info, lookup
            if not yahoo_symbol or not name:
                if xtb_symbol in symbol_cache:
                    info = symbol_cache[xtb_symbol]
                else:
                    # Convert suffix first
                    y_sym = convert_xtb_suffix(xtb_symbol)
                    info = get_symbol_info(y_sym)
                    symbol_cache[xtb_symbol] = info
                    time.sleep(0.2) # Rate limit
                
                if not yahoo_symbol:
                    yahoo_symbol = info.get('symbol', '')
                if not name:
                    name = info.get('name', '')
                if not currency:
                    currency = info.get('currency', '')
        
        # Determine Value and Currency
        # Default: Use Amount (EUR)
        value = abs(amount)
        txn_currency = 'EUR'
        exchange_rate = ''
        
        # Try to find original currency match for Buy/Sell
        if pp_type in ['Buy', 'Sell'] and xtb_symbol:
            is_open = (pp_type == 'Buy')
            match = _find_position_match(positions, xtb_symbol, dt, is_open)
            
            if match:
                price = match['open_price'] if is_open else match['close_price']
                vol = match['volume']
                
                # If we have price and volume, we can calculate original value
                if price is not None and vol is not None:
                    try:
                        price = float(price)
                        vol = float(vol)
                        original_value = price * vol
                        
                        # Use symbol currency if available
                        if currency:
                            txn_currency = currency
                            value = original_value
                            
                            # Calculate exchange rate: EUR Amount / Original Value
                            if original_value != 0:
                                exchange_rate = str(abs(amount) / original_value)
                                
                            # Update shares from position if available (more reliable?)
                            if vol > 0:
                                shares = vol
                                
                    except (ValueError, TypeError):
                        pass
        
        # Construct Output Row
        out_row = {
            'Date': date_str,
            'Time': time_str,
            'Type': pp_type,
            'Value': value,
            'Shares': shares,
            'Fees': 0.0,
            'Taxes': 0.0,
            'Transaction Currency': txn_currency,
            'Exchange Rate': exchange_rate,
            'ISIN': '', # XTB doesn't provide ISIN in Cash Ops easily
            'Ticker Symbol': yahoo_symbol,
            'Security Name': name,
            'Note': f"XTB: {comment}",
            'Cash Account': cash_account,
            'Securities Account': securities_account
        }
        
        output_rows.append(out_row)
        
    # Create DataFrame
    out_df = pd.DataFrame(output_rows)
    
    logger.info(f"Total transactions: {len(out_df)}")
    
    return out_df
