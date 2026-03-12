import re
from typing import Optional


def format_inr(amount: float) -> str:
    if amount >= 10000000:
        return f"Rs.{amount / 10000000:.2f} Cr"
    elif amount >= 100000:
        return f"Rs.{amount / 100000:.2f} L"
    return f"Rs.{amount:,.2f}"


def sanitize_customer_id(customer_id: str) -> str:
    customer_id = customer_id.strip().upper()
    if not re.match(r"^CUST\d{4}$", customer_id):
        raise ValueError(f"Invalid customer ID: {customer_id}. Expected CUST####")
    return customer_id


def safe_get(d: dict, *keys, default=None):
    result = d
    for key in keys:
        if not isinstance(result, dict):
            return default
        result = result.get(key, default)
    return result