import requests
import os
from typing import Optional

PRICECHARTING_TOKEN = os.getenv('PRICECHARTING_TOKEN')

def product_exists(product_id: int, timeout: float = 5.0) -> Optional[bool]:
    """
    Practical: Return False if HTTP 404 OR API JSON explicitly says "No such product".
    Return True if 200 and no explicit API error. Return None if unknown (network/server issues).
    """
    url = "https://www.pricecharting.com/api/product"
    params = {"t": PRICECHARTING_TOKEN, "id": str(product_id)}

    try:
        resp = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException:
        return None

    if resp.status_code == 404:
        return False

    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
    except ValueError:
        return None

    if isinstance(data, dict):
        status = (data.get("status") or "").lower()
        err_text = ((data.get("error") or "") + (data.get("error-message") or "")).lower()

        if status == "error":
            # Explicit "No such product" -> definitely not found
            if "no such product" in err_text:
                return False
            # Some other API error -> unknown (caller may want to retry or log)
            return None

    # 200 + no explicit API error -> assume exists
    return True
