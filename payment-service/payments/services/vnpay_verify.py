"""
Verify VNPAY callback (return URL + IPN): HMAC-SHA512 on sorted vnp_* fields.
"""
import hashlib
import hmac
import os
from typing import Any

from .vnpay import _vnpay_sign


def merge_vnp_params(request) -> dict[str, str]:
    """Collect vnp_* parameters from GET and POST (form)."""
    out: dict[str, str] = {}

    def _take(source):
        if not source:
            return
        keys = source.keys() if hasattr(source, 'keys') else []
        for key in keys:
            if not str(key).startswith('vnp_'):
                continue
            if hasattr(source, 'getlist'):
                vals = source.getlist(key)
                out[str(key)] = str(vals[-1]) if vals else ''
            else:
                out[str(key)] = str(source.get(key))

    _take(request.GET)
    _take(request.POST)
    return out


def verify_vnpay_signature(params: dict[str, str], hash_secret: str) -> bool:
    received = (params.get('vnp_SecureHash') or '').strip()
    if not received:
        return False
    sign_input = {k: v for k, v in params.items() if k not in ('vnp_SecureHash', 'vnp_SecureHashType')}
    expected = _vnpay_sign(sign_input, hash_secret)
    return hmac.compare_digest(expected.lower(), received.lower())


def parse_txn_ref(txn_ref: str) -> tuple[int, int] | None:
    """Parse vnp_TxnRef: 'order_idPpayment_id' (current) or legacy 'order_id-payment_id'."""
    if not txn_ref:
        return None
    if 'P' in txn_ref:
        left, right = txn_ref.split('P', 1)
        try:
            return int(left), int(right)
        except ValueError:
            return None
    if '-' in txn_ref:
        left, right = txn_ref.rsplit('-', 1)
        try:
            return int(left), int(right)
        except ValueError:
            return None
    return None
