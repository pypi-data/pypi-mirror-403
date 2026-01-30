import argparse

import pandas as pd

from .converters import get_converter_for_file
from .utils import setup_logger

logger = setup_logger('cli')

def run_cli(args=None):
    """
    Main entry point for the CLI interface.
    
    Args:
        args: Optional list of arguments to parse. If None, sys.argv[1:] is used.
    """
    parser = argparse.ArgumentParser(description='Broker to Portfolio Performance Converter')
    parser.add_argument('--input', '-i', required=True, nargs='+', help='Path to input file(s)')
    parser.add_argument('--output', '-o', required=True, help='Path to output consolidated CSV file')
    parser.add_argument('--config', '-c', default='config.yaml', help='Path to config.yaml')

    # If args is passed (e.g. from tests), use it. Otherwise uses sys.argv automatically.
    parsed_args = parser.parse_args(args)

    all_results = []
    for file_path in parsed_args.input:
        converter = get_converter_for_file(file_path)
        if not converter:
            logger.error(f"Could not identify provider for file {file_path}")
            continue
        
        logger.info(f"Detected {converter.name} for {file_path}")
        
        try:
            df = converter.convert(file_path, parsed_args.config)
            if df is not None and not df.empty:
                all_results.append(df)
        except Exception as e:
            logger.error(f"Error converting {file_path}: {e}")
    
    if all_results:
        consolidated = pd.concat(all_results, ignore_index=True)
        if 'Date' in consolidated.columns:
            consolidated = consolidated.sort_values('Date').reset_index(drop=True)
        consolidated.to_csv(parsed_args.output, index=False)
        logger.info(f"Exported consolidated data to {parsed_args.output}")
    else:
        logger.warning("No data to export")
