import re
from decimal import Decimal


SALARY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*[kK]\s*[-~]\s*(\d+(?:\.\d+)?)\s*[kK]")


def parse_salary_range(salary_text: str | None) -> tuple[Decimal | None, Decimal | None, str | None, str | None]:
    if not salary_text:
        return None, None, None, None

    text = salary_text.replace("·", "").replace(" ", "")
    match = SALARY_PATTERN.search(text)
    if not match:
        return None, None, "CNY", "month"

    low, high = Decimal(match.group(1)) * 1000, Decimal(match.group(2)) * 1000
    period = "month"
    if "年" in text or "year" in text.lower():
        period = "year"
    return low, high, "CNY", period
