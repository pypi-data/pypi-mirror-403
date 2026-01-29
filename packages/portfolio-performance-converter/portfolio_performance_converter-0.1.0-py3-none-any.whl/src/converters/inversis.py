import time
from typing import Optional

import pandas as pd

from ..market_data import lookup_isin_info
from ..utils import load_config, parse_number, setup_logger
from .base import BaseConverter

logger = setup_logger(__name__)

class InversisConverter(BaseConverter):
    @property
    def name(self) -> str:
        return "Inversis"

    @property
    def instructions(self) -> str:
        return """
        <div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 5px;">
            <p><strong>Step-by-step instructions:</strong></p>
            <ol style="margin-left: 20px;">
                <li>Log in to the <b>Inversis</b> platform. For example, for Inversis for MyInvestor <a href="https://www.inversis.com/index.html?cobranding=cbmyinvestor">here</a>.</li>
                <li>Go to <b>Inversiones</b> > <b>Fondos</b> (or <b>ETFs</b> or <b>Acciones</b>) > <b>Operaciones y consultas</b> > <b>Consulta de operaciones</b>.</li>
                <li>Select the <b>time range</b>, <b>product type</b> and other relevant filters.</li>
                <li>Click the <b>Iniciar Búsqueda</b> button.</li>
                <li>Download the table using the top-right <b>Excel</b> button.</li>
            </ol>
        </div>
        """

    @property
    def input_data_types(self) -> list[dict]:
        return [
            {"field_name": "Fechas", "field_type": "Date", "description": "Date of the operation", "example": "01/01/2023"},
            {"field_name": "Operación", "field_type": "String", "description": "Type of operation", "example": "Compra"},
            {"field_name": "Nombre", "field_type": "String", "description": "Name of the asset", "example": "Fondo X"},
            {"field_name": "Importe", "field_type": "Decimal", "description": "Total amount", "example": "1000,00"},
            {"field_name": "Participaciones", "field_type": "Decimal", "description": "Number of shares", "example": "10,5"},
            {"field_name": "Precio", "field_type": "Decimal", "description": "Price per share", "example": "100,00"},
            {"field_name": "Divisa", "field_type": "String", "description": "Currency", "example": "EUR"},
        ]

    def detect(self, input_path: str) -> bool:
        """Check if the file is an Inversis XLS export."""
        try:
            # Inversis "XLS" is often an HTML table
            dfs = pd.read_html(input_path)
            if dfs:
                df = dfs[0]
                # Check for MultiIndex or specific columns
                cols = str(df.columns.tolist())
                return 'Fechas' in cols and 'Operación' in cols
            return False
        except Exception:
            try:
                # Fallback to real Excel
                df = pd.read_excel(input_path, nrows=5)
                cols = str(df.columns.tolist())
                return 'Fechas' in cols and 'Operación' in cols
            except Exception:
                return False

    def _convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """Convert Inversis HTML/XLS export to Portfolio Performance CSV format."""
        return convert_inversis(
            input_path, 
            config_path=config_path,
            cash_account='',
            securities_account=''
        )

def convert_inversis(
    input_path: str, 
    config_path: Optional[str] = None, 
    cash_account: str = '', 
    securities_account: str = ''
) -> pd.DataFrame:
    """Convert Inversis HTML/XLS export to Portfolio Performance CSV format."""
    
    try:
        # Inversis "XLS" is often an HTML table
        # It seems to use dot for decimals based on inspection
        dfs = pd.read_html(input_path)
        if not dfs:
            logger.error(f"No tables found in {input_path}")
            return pd.DataFrame()
        df = dfs[0]
    except Exception as e:
        # Fallback to read_excel if it's a real Excel file
        try:
            df = pd.read_excel(input_path)
        except Exception as e2:
            logger.error(f"Failed to read file {input_path}: {e} / {e2}")
            return pd.DataFrame()

    # Handle MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten columns: take the second level if it exists and is not empty, else first
        # Based on inspection: 
        # ('Fechas', 'Operación') -> Date
        # ('Operación', 'Operación.1') -> Type
        # ('ISIN', 'ISIN') -> ISIN
        # ('Importe neto', 'Importe neto') -> Value
        
        # Let's just map by position as the names are a bit messy
        # Expected columns based on inspection:
        # 0: Date (Fechas, Operación)
        # 1: Settlement Date (Fechas, Liquidación)
        # 2: Transaction ID (Operación, Operación)
        # 3: Market (Mercado, Mercado)
        # 4: Type (Operación, Operación.1)
        # 5: ISIN (ISIN, ISIN)
        # 6: Name (Valor, Valor)
        # 7: Shares (Títulos/NOMINAL, Títulos/NOMINAL)
        # 8: Currency (Divisa, Divisa)
        # 9: Price (Precio Neto, Precio Neto)
        # 10: Value (Importe neto, Importe neto)
        
        if len(df.columns) >= 11:
            df.columns = [
                'Date', 'SettlementDate', 'TransactionID', 'Market', 'Type', 
                'ISIN', 'Name', 'Shares', 'Currency', 'Price', 'Value'
            ]
        else:
            logger.error(f"Unexpected column count: {len(df.columns)}")
            return pd.DataFrame()
    else:
        # If not MultiIndex, try to map by name or position
        # For now assume the structure is consistent
        if len(df.columns) >= 11:
            df.columns = [
                'Date', 'SettlementDate', 'TransactionID', 'Market', 'Type', 
                'ISIN', 'Name', 'Shares', 'Currency', 'Price', 'Value'
            ]

    # Filter out empty rows or summary rows
    df = df.dropna(subset=['Date', 'ISIN'])

    # Parse Date
    def parse_date(d):
        try:
            # Inversis format seems to be YYYY-MM-DD based on pandas output in inspection
            # But if pandas parsed it as datetime, we just format it.
            # If it's string, we might need to parse.
            if isinstance(d, pd.Timestamp):
                return d.date().isoformat()
            return pd.to_datetime(d).date().isoformat()
        except Exception:
            return str(d)

    df['Date'] = df['Date'].apply(parse_date)

    # Map Transaction Types
    def map_type(t):
        t = str(t).upper()
        if 'SUSCR' in t or 'COMPRA' in t:
            return 'Buy'
        if 'REEMB' in t or 'VENTA' in t:
            return 'Sell'
        return 'Buy' # Default

    df['Type'] = df['Type'].apply(map_type)

    # Ensure numeric columns are float
    # If read_html handled it, they are already float. If not, parse.
    for col in ['Shares', 'Price', 'Value']:
        if df[col].dtype == object:
            df[col] = df[col].apply(parse_number)

    # Load configuration for overrides
    config = load_config(config_path)
    overrides = config.get('overrides', {})
    
    # ISIN Lookup and Enrichment
    cache: dict[str, dict[str, str]] = {}
    symbols = []
    names = []
    
    for _idx, row in df.iterrows():
        isin = str(row['ISIN']).strip()
        info = {'symbol': '', 'name': ''}
        
        if isin in overrides:
            override = overrides[isin]
            info['symbol'] = override.get('symbol', '')
            info['name'] = override.get('name', '')
            
            if not info['symbol'] or not info['name']:
                fetched = {}
                if isin in cache:
                    fetched = cache[isin]
                else:
                    fetched = lookup_isin_info(isin)
                    cache[isin] = fetched
                    time.sleep(0.3)
                
                if not info['symbol']:
                    info['symbol'] = fetched.get('symbol', '')
                if not info['name']:
                    info['name'] = fetched.get('name', '')
        else:
            if isin in cache:
                info = cache[isin]
            else:
                info = lookup_isin_info(isin)
                cache[isin] = info
                time.sleep(0.3)
        
        symbols.append(info.get('symbol', ''))
        names.append(info.get('name', ''))

    df['Symbol'] = symbols
    df['Name_API'] = names
    
    # Use API/Override name if available, else fallback to original Name
    df['FinalName'] = df.apply(lambda r: r['Name_API'] if r['Name_API'] else r['Name'], axis=1)

    # Build Portfolio Performance dataframe
    out = pd.DataFrame()
    out['Date'] = df['Date']
    out['Time'] = ''
    out['Type'] = df['Type']
    out['Value'] = df['Value'].abs()
    out['Shares'] = df['Shares']
    out['Fees'] = 0.0
    out['Taxes'] = 0.0
    out['Transaction Currency'] = df['Currency']
    out['Exchange Rate'] = ''
    out['ISIN'] = df['ISIN']
    out['Ticker Symbol'] = df['Symbol']
    out['Security Name'] = df['FinalName']
    out['WKN'] = ''
    out['Note'] = 'Inversis: ' + df['TransactionID'].astype(str) + ' - ' + df['Market']
    out['Cash Account'] = cash_account
    out['Securities Account'] = securities_account

    return out
