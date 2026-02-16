from app.utils.salary import parse_salary_range


def test_parse_salary_range_k() -> None:
    low, high, currency, period = parse_salary_range("25k-40k/月")
    assert float(low) == 25000
    assert float(high) == 40000
    assert currency == "CNY"
    assert period == "month"
