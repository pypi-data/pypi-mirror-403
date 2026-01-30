from typing import Dict

import yfinance as yf  # type: ignore


def convert_xtb_suffix(symbol: str) -> str:
    """Convert XTB symbol suffix to Yahoo Finance suffix."""
    if not symbol or not isinstance(symbol, str):
        return ''
    
    # Common mappings
    suffix_map = {
        '.US': '', # US stocks usually don't have suffix in YF
        '.ES': '.MC',
        '.DE': '.DE', # Often same
        '.UK': '.L',
        '.FR': '.PA',
        '.NL': '.AS',
        '.PT': '.LS',
        '.IT': '.MI',
        '.BE': '.BR'
    }
    
    for xtb_suffix, yf_suffix in suffix_map.items():
        if symbol.endswith(xtb_suffix):
            return symbol[:-len(xtb_suffix)] + yf_suffix
            
    return symbol

def get_symbol_info(symbol: str) -> Dict[str, str]:
    """
    Fetches information from Yahoo Finance for a given symbol.
    Returns a dict with: symbol, name, currency
    """
    info = {'symbol': symbol, 'name': '', 'currency': ''}
    
    if not symbol:
        return info

    try:
        ticker = yf.Ticker(symbol)
        t_info = ticker.info
        if t_info:
            info['currency'] = t_info.get('currency', '')
            # Try different name fields
            info['name'] = t_info.get('shortName') or t_info.get('longName') or ''
    except Exception:
        # Log error or ignore
        pass
        
    return info

def lookup_isin_info(isin: str) -> Dict[str, str]:
    """
    Searches Yahoo Finance by ISIN.
    Returns a dict with: symbol, name, currency
    """
    info = {'symbol': '', 'name': '', 'currency': ''}
    
    try:
        search_results = yf.Search(isin, max_results=1).quotes
        
        if search_results:
            res = search_results[0]
            info['symbol'] = res.get('symbol', '')
            
            s_name = res.get('shortname', '')
            l_name = res.get('longname', '')
            
            # Prefer longname if shortname is same as symbol or missing
            if s_name and s_name != info['symbol']:
                info['name'] = s_name
            else:
                info['name'] = l_name or s_name
            
            # If we found a symbol, try to get currency details
            if info['symbol']:
                details = get_symbol_info(info['symbol'])
                if details['currency']:
                    info['currency'] = details['currency']
                    
    except Exception:
        pass
        
    return info
