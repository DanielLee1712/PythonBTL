import os

import requests


def adjust_product_stock(product_id: int, delta: int) -> dict:
    """
    Call product-service to change stock by delta (negative = reserve / sell).
    Returns parsed JSON on success.
    """
    base = os.environ.get('PRODUCT_SERVICE_BASE_URL', 'http://127.0.0.1:8001').rstrip('/')
    url = f'{base}/api/v1/products/adjust-stock/'
    resp = requests.post(
        url,
        json={'product_id': product_id, 'delta': delta},
        timeout=15,
    )
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = {'detail': resp.text}
        err = requests.HTTPError(str(detail))
        err.response = resp
        raise err
    return resp.json()
