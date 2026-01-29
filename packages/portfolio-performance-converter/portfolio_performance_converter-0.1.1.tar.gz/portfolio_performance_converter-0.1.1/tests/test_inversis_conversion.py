from src.converters.inversis import convert_inversis
from src.utils import setup_logger

logger = setup_logger('test_inversis')

def test_conversion(tmp_path):
    input_file = 'tests/data/inversis_investments.xls'
    output_file = tmp_path / 'test_output.csv'
    
    logger.info(f"Testing conversion of {input_file}...")
    
    try:
        df = convert_inversis(
            input_file, 
            cash_account='Test Cash', 
            securities_account='Test Securities'
        )
        
        if df is not None and not df.empty:
            logger.info("Conversion successful!")
            print(df.head().to_string())
            print("\nColumns:", df.columns.tolist())
            df.to_csv(output_file, index=False)
            logger.info(f"Saved to {output_file}")
        else:
            logger.error("Conversion returned empty DataFrame")
            
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion()
