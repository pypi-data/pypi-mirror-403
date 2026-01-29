import pytest
import yfinance as yf


@pytest.mark.parametrize("isin", ["IE0032126645"])
def test_isin_lookup(isin):
    print(f"Searching for {isin}...")
    try:
        search_results = yf.Search(isin, max_results=10).quotes
        print(f"Found {len(search_results)} results via yf.Search:")
        
        assert len(search_results) > 0, f"No results found for ISIN {isin}"
        
        for res in search_results:
            print(f"  Symbol: {res['symbol']}, Exchange: {res['exchange']}, ShortName: {res.get('shortname')}")
            assert 'symbol' in res, "Result missing symbol"

    except Exception as e:
        pytest.fail(f"yf.Search failed: {e}")

