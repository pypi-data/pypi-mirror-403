from sdata import SDataClient


def test_call_api():
    client = SDataClient("http://localhost:8081")
    result = client.call_api("get_price", {"security": "000001.XSHE", "start_date": "2025-06-10", "end_date": "2025-08-01"})
    print(result)
    assert result is not None
