import os

from src.converters import get_converter_for_file


def test_detect_myinvestor():
    path = 'tests/data/myinvestor_orders.csv'
    if os.path.exists(path):
        converter = get_converter_for_file(path)
        assert converter is not None
        assert converter.name == 'MyInvestor'

def test_detect_xtb():
    path = 'tests/data/xtb_account.xlsx'
    if os.path.exists(path):
        converter = get_converter_for_file(path)
        assert converter is not None
        assert converter.name == 'XTB'

def test_detect_inversis():
    path = 'tests/data/inversis_investments.xls'
    if os.path.exists(path):
        converter = get_converter_for_file(path)
        assert converter is not None
        assert converter.name == 'Inversis'

def test_detect_unknown():
    # Create a dummy file
    with open('unknown.csv', 'w') as f:
        f.write("col1,col2\nval1,val2")
    
    converter = get_converter_for_file('unknown.csv')
    assert converter is None
    
    os.remove('unknown.csv')
