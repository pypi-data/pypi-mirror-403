import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

try:
    import yaml
except ImportError:
    yaml = None # type: ignore

def setup_logger(name: str) -> logging.Logger:
    """Configures and returns a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load YAML configuration with overrides."""
    if yaml is None:
        return {'overrides': {}}
    
    if config_path is None:
        # Default to config.yaml in the root if not specified
        # Assuming this is run from root or we need to find it relative to this file
        # For now, let's assume root or passed explicitly
        config_path = 'config.yaml'
    
    path_obj = Path(config_path)
    
    if not path_obj.exists():
        return {'overrides': {}}
    
    try:
        with open(path_obj, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        return cfg
    except Exception as e:
        print(f"WARNING: Could not load config file {config_path}: {e}")
        return {'overrides': {}}

def parse_number(text: Any) -> float:
    """Parses a number from string, handling various formats (comma/dot)."""
    if pd.isna(text):
        return 0.0
    if isinstance(text, (int, float)):
        return float(text)
        
    s = str(text).strip()
    # If it has both comma and dot, assume the last one is decimal separator
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
        
    try:
        return float(s)
    except Exception:
        return 0.0

def parse_currency_string(text: str) -> Tuple[float, Optional[str]]:
    """Extracts amount and currency from a string like '1.234,56 EUR'."""
    if not isinstance(text, str):
        return 0.0, None
    
    # Regex to find number and optional 3-letter currency code
    m = re.search(r"([\d\.,]+)\s*([A-Za-z]{3})?", text)
    if not m:
        return 0.0, None
        
    num_part = m.group(1)
    currency_part = m.group(2)
    
    val = parse_number(num_part)
    
    return val, currency_part
