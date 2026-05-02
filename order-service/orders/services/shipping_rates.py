"""Server-side shipping options and fees (VND)."""

SHIPPING_OPTIONS = {
    'standard': {'label': 'Standard (3–5 days)', 'fee': 30000},
    'express': {'label': 'Express (1–2 days)', 'fee': 60000},
    'same_day': {'label': 'Same day (within city)', 'fee': 120000},
}


def fee_for_method(method: str) -> int:
    opt = SHIPPING_OPTIONS.get(method)
    if opt is None:
        raise ValueError(f'Unknown shipping_method: {method}')
    return int(opt['fee'])


def label_for_method(method: str) -> str:
    return SHIPPING_OPTIONS.get(method, {}).get('label', method)
