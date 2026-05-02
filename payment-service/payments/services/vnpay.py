"""
Build VNPAY payment redirect URL (Payment v2 / vpcpay).
Hash string: sorted vnp_* (except vnp_SecureHash / vnp_SecureHashType), each pair
PHP urlencode(key)=urlencode(value) joined with &, then HMAC-SHA512 (VNPAY 2.1.0 docs).
"""
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from zoneinfo import ZoneInfo


def _clean_env(value: str | None) -> str:
    """Strip BOM/CR and optional wrapping quotes from .env / Docker values."""
    if value is None:
        return ''
    s = str(value).strip().strip('\ufeff').replace('\r', '')
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return s


def _php_urlencode(value: str) -> str:
    """
    Match PHP urlencode() for VNPAY HMAC: UTF-8 percent-encoding, spaces as '+'.
    PHP encodes '~' as %7E; urllib.parse.quote keeps '~' unquoted by default.
    """
    s = quote(str(value), safe='', encoding='utf-8').replace('%20', '+').replace('~', '%7E')
    return s


def _skip_ipn_url(url: str) -> bool:
    """Localhost IPN is unreachable by VNPAY; some gateways normalize params and break the hash."""
    if (os.environ.get('VNPAY_INCLUDE_LOCAL_IPN') or '').strip() == '1':
        return False
    u = (url or '').strip().lower()
    return (not u) or 'localhost' in u or '127.0.0.1' in u


def vnpay_configured() -> bool:
    tmn = _clean_env(os.environ.get('VNPAY_TMN_CODE'))
    sec = _clean_env(os.environ.get('VNPAY_HASH_SECRET'))
    ret = _clean_env(os.environ.get('VNPAY_RETURN_URL'))
    return bool(tmn and sec and ret)


def _amount_cents_vnd(order_total) -> int:
    """VNPAY: amount in VND * 100 (no decimal in payload)."""
    try:
        d = Decimal(str(order_total))
    except (InvalidOperation, TypeError, ValueError):
        d = Decimal('0')
    return int(d * 100)


def _sign_keys(params: dict[str, str]) -> list[str]:
    return sorted(
        k
        for k in params
        if k.startswith('vnp_')
        and k not in ('vnp_SecureHash', 'vnp_SecureHashType')
        and params[k] is not None
        and str(params[k]) != ''
    )


def _vnpay_sign(params: dict[str, str], hash_secret: str) -> str:
    """Build HMAC-SHA512 over PHP urlencode() sorted field string (VNPAY 2.1.0)."""
    keys = _sign_keys(params)
    payload = '&'.join(
        f'{_php_urlencode(k)}={_php_urlencode(str(params[k]))}'
        for k in keys
    )
    return hmac.new(
        hash_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()


def _build_sorted_query(params: dict[str, str]) -> str:
    """Sorted query string; same encoding as hash string (VNPAY spec)."""
    keys = sorted(params.keys())
    return '&'.join(
        f'{_php_urlencode(k)}={_php_urlencode(str(params[k]))}'
        for k in keys
    )


def build_vnpay_payment_url(
    *,
    order_id: int,
    payment_id: int,
    order_total,
    order_info: str,
    client_ip: str,
) -> tuple[str, str]:
    """
    Returns (full_redirect_url, vnp_TxnRef).
    """
    tmn = _clean_env(os.environ.get('VNPAY_TMN_CODE'))
    secret = _clean_env(os.environ.get('VNPAY_HASH_SECRET'))
    pay_url = _clean_env(
        os.environ.get('VNPAY_PAY_URL') or 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
    )
    return_url = _clean_env(os.environ.get('VNPAY_RETURN_URL'))
    ipn_url = _clean_env(os.environ.get('VNPAY_IPN_URL'))
    version = _clean_env(os.environ.get('VNPAY_VERSION') or '2.1.0')
    command = _clean_env(os.environ.get('VNPAY_COMMAND') or 'pay')
    locale = _clean_env(os.environ.get('VNPAY_LOCALE') or 'vn')
    curr = _clean_env(os.environ.get('VNPAY_CURR_CODE') or 'VND')
    order_type = _clean_env(os.environ.get('VNPAY_ORDER_TYPE') or 'other')
    ip_fallback = _clean_env(os.environ.get('VNPAY_IP_ADDR_FALLBACK') or '127.0.0.1')
    if not tmn or not secret or not return_url:
        raise KeyError('VNPAY_TMN_CODE, VNPAY_HASH_SECRET, VNPAY_RETURN_URL are required')

    tz = ZoneInfo('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    create = now.strftime('%Y%m%d%H%M%S')
    expire = (now + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S')

    # Alphanumeric ref; 'P' separator (parsed in vnpay_verify); avoid '-' ambiguity with VNPAY samples
    vnp_txn_ref = f'{order_id}P{payment_id}'[:100]
    amount = _amount_cents_vnd(order_total)
    if amount <= 0:
        raise ValueError('Invalid order amount for VNPAY')

    raw_ip = (client_ip or '').strip() or ip_fallback
    if ':' in raw_ip and '.' not in raw_ip:
        raw_ip = ip_fallback
    vnp_ip = raw_ip[:45]

    params: dict[str, str] = {
        'vnp_Version': version,
        'vnp_Command': command,
        'vnp_TmnCode': tmn,
        'vnp_Locale': locale,
        'vnp_CurrCode': curr,
        'vnp_TxnRef': vnp_txn_ref,
        'vnp_OrderInfo': (order_info or f'Thanh toan don hang #{order_id}')[:255],
        'vnp_OrderType': order_type,
        'vnp_Amount': str(amount),
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': vnp_ip,
        'vnp_CreateDate': create,
        'vnp_ExpireDate': expire,
    }
    if ipn_url and not _skip_ipn_url(ipn_url):
        params['vnp_IpnUrl'] = ipn_url[:800]

    secure_hash = _vnpay_sign(params, secret)
    params_with_hash = {**params, 'vnp_SecureHash': secure_hash}
    query = _build_sorted_query(params_with_hash)
    return f'{pay_url}?{query}', vnp_txn_ref
