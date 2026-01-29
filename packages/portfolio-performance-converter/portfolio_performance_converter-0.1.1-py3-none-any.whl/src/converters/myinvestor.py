import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from ..market_data import lookup_isin_info
from ..utils import load_config, parse_currency_string, parse_number, setup_logger
from .base import BaseConverter

logger = setup_logger(__name__)

class MyInvestorConverter(BaseConverter):
    @property
    def name(self) -> str:
        return "MyInvestor"

    @property
    def instructions(self) -> Optional[str]:
        return None

    @property
    def input_data_types(self) -> list[dict]:
        return [
            {"field_name": "Fecha de la orden", "field_type": "Date", "description": "Date of the order", "example": "01/01/2023"},
            {"field_name": "Tipo de orden", "field_type": "String", "description": "Type", "example": "Compra"},
            {"field_name": "ISIN", "field_type": "String", "description": "ISIN code", "example": "ES0123456789"},
            {"field_name": "Nombre de valor", "field_type": "String", "description": "Asset name", "example": "ACME Corp"},
            {"field_name": "Número de títulos", "field_type": "Decimal", "description": "Quantity", "example": "50"},
            {"field_name": "Precio", "field_type": "Decimal", "description": "Price per unit", "example": "20.5"},
            {"field_name": "Importe", "field_type": "Decimal", "description": "Total amount", "example": "1000"},
        ]

    def detect(self, input_path: str) -> bool:
        """Check if the file is a MyInvestor CSV."""
        try:
            # MyInvestor uses semicolon separator and utf-8-sig encoding
            df = pd.read_csv(input_path, sep=';', encoding='utf-8-sig', nrows=5)
            return 'Fecha de la orden' in [c.strip() for c in df.columns]
        except Exception:
            return False

    def _convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """Convert a single MyInvestor CSV to Portfolio Performance CSV format."""
        return convert_single_myinvestor(
            input_path, 
            config_path=config_path,
            cash_account='',
            securities_account=''
        )

def convert_single_myinvestor(
    input_path: str, 
    config_path: Optional[str] = None, 
    assume_transaction_type: str = 'Buy',
    cash_account: str = '', 
    securities_account: str = ''
) -> pd.DataFrame:
    """Convert a single MyInvestor CSV to Portfolio Performance CSV format."""
    
    try:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8-sig')
    except Exception as e:
        logger.error(f"Failed to read CSV {input_path}: {e}")
        return pd.DataFrame()

    # Normalize column names (strip)
    df.columns = [c.strip() for c in df.columns]

    # Required columns check could be added here

    # Parse trade date DD/MM/YYYY -> YYYY-MM-DD
    def parse_date(d):
        try:
            return datetime.strptime(str(d).strip(), '%d/%m/%Y').date().isoformat()
        except Exception:
            return d

    if 'Fecha de la orden' in df.columns:
        df['Date'] = df['Fecha de la orden'].apply(parse_date)
    else:
        logger.warning(f"Column 'Fecha de la orden' not found in {input_path}")
        return pd.DataFrame()

    df['ISIN'] = df['ISIN'].astype(str).str.strip() if 'ISIN' in df.columns else ''

    # Parse importe and currency
    if 'Importe estimado' in df.columns:
        df[['Value', 'importe_currency']] = df['Importe estimado'].apply(
            lambda x: pd.Series(parse_currency_string(str(x)))
        )
    else:
        df['Value'] = 0.0
        df['importe_currency'] = None

    # Parse number of shares
    if 'Nº de participaciones' in df.columns:
        df['Shares'] = df['Nº de participaciones'].apply(parse_number)
    else:
        df['Shares'] = 0.0

    df['Type'] = assume_transaction_type

    # Load configuration with ISIN overrides
    config = load_config(config_path)
    overrides = config.get('overrides', {})

    # Lookup symbol, name, currency via Yahoo Finance (cached)
    cache: dict[str, dict[str, str]] = {}
    symbols = []
    names = []
    currencies = []
    
    for isin in df['ISIN']:
        info = {'symbol': '', 'name': '', 'currency': ''}
        
        # Check for overrides first
        if isin in overrides:
            override = overrides[isin]
            info['symbol'] = override.get('symbol', '')
            info['name'] = override.get('name', '')
            info['currency'] = override.get('currency', '')
            
            # If override is partial, try to fetch missing info
            if not info['symbol'] or not info['name']:
                fetched = {}
                if isin in cache:
                    fetched = cache[isin]
                else:
                    fetched = lookup_isin_info(isin)
                    cache[isin] = fetched
                    time.sleep(0.3) # Rate limiting
                
                if not info['symbol']:
                    info['symbol'] = fetched.get('symbol', '')
                if not info['name']:
                    info['name'] = fetched.get('name', '')
                if not info['currency']:
                    info['currency'] = fetched.get('currency', '')
        else:
            if isin in cache:
                info = cache[isin]
            else:
                info = lookup_isin_info(isin)
                cache[isin] = info
                time.sleep(0.3)
        
        symbols.append(info.get('symbol', ''))
        names.append(info.get('name', ''))
        currencies.append(info.get('currency', ''))

    df['Symbol'] = symbols
    df['Name'] = names
    
    # Prefer currency from API/override, otherwise use parsed importe currency
    df['Currency'] = [c if c else cur2 for c, cur2 in zip(currencies, df['importe_currency'], strict=False)]
    
    if 'Estado' in df.columns:
        df['Note'] = "MyInvestor: " + df['Estado'].astype(str)
    else:
        df['Note'] = "MyInvestor: "

    # Build Portfolio Performance dataframe
    out = pd.DataFrame()
    out['Date'] = df['Date']
    out['Time'] = ''
    out['Type'] = df['Type']
    out['Value'] = df['Value']
    out['Shares'] = df['Shares']
    out['Fees'] = 0.0
    out['Taxes'] = 0.0
    out['Transaction Currency'] = df['Currency']
    out['Exchange Rate'] = ''
    out['ISIN'] = df['ISIN']
    out['Ticker Symbol'] = df['Symbol']
    out['Security Name'] = df['Name']
    out['WKN'] = ''
    out['Note'] = df['Note']
    out['Cash Account'] = cash_account
    out['Securities Account'] = securities_account

    return out

def process_myinvestor_folder(
    input_dir: str, 
    config_path: Optional[str] = None, 
    assume_transaction_type: str = 'Buy',
    cash_account: str = '', 
    securities_account: str = ''
) -> pd.DataFrame:
    """Convert all CSV files in a folder to a single consolidated DataFrame."""
    input_folder = Path(input_dir)
    
    if not input_folder.is_dir():
        logger.error(f"{input_dir} is not a directory")
        return pd.DataFrame()
    
    csv_files = list(input_folder.glob('*.csv'))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {input_dir}")
        return pd.DataFrame()
    
    logger.info(f"Processing {len(csv_files)} files from {input_dir}...")
    
    all_results = []
    
    for csv_file in sorted(csv_files):
        try:
            logger.info(f"Reading: {csv_file.name}")
            out = convert_single_myinvestor(
                str(csv_file), 
                config_path, 
                assume_transaction_type, 
                cash_account, 
                securities_account
            )
            if not out.empty:
                all_results.append(out)
        except Exception as e:
            logger.error(f"Error processing {csv_file.name}: {e}")
    
    if all_results:
        consolidated = pd.concat(all_results, ignore_index=True)
        consolidated = consolidated.sort_values('Date').reset_index(drop=True)
        return consolidated
    else:
        return pd.DataFrame()
