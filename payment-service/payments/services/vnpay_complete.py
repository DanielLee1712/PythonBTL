"""
Shared logic for VNPAY return URL + IPN: verify signature, amount, then mark order paid.
"""
import os

import requests
from django.db import transaction

from ..models import Payment
from .vnpay import _amount_cents_vnd, _clean_env, vnpay_configured
from .vnpay_verify import parse_txn_ref, verify_vnpay_signature


def _order_base() -> str:
    return os.environ.get('ORDER_SERVICE_BASE_URL', 'http://127.0.0.1:8005').rstrip('/')


def _sync_payment_completed(payment_id: int) -> None:
    with transaction.atomic():
        p2 = Payment.objects.select_for_update().get(pk=payment_id)
        if p2.status != Payment.Status.COMPLETED:
            p2.status = Payment.Status.COMPLETED
            p2.save(update_fields=['status'])


def try_complete_vnpay_payment(params: dict[str, str]) -> tuple[str, str]:
    """
    Verify VNPAY payload and mark order paid when successful.
    Returns (RspCode, Message) for IPN JSON; RspCode '00' = OK for VNPAY.
    """
    if not vnpay_configured():
        return '97', 'VNPAY not configured'

    secret = _clean_env(os.environ.get('VNPAY_HASH_SECRET'))
    if not verify_vnpay_signature(params, secret):
        return '97', 'Invalid signature'

    tmn = (params.get('vnp_TmnCode') or '').strip()
    if tmn != _clean_env(os.environ.get('VNPAY_TMN_CODE')):
        return '97', 'Invalid TmnCode'

    txn_ref = (params.get('vnp_TxnRef') or '').strip()
    if not txn_ref:
        return '01', 'Missing vnp_TxnRef'

    payment = Payment.objects.filter(vnp_txn_ref=txn_ref).first()
    if not payment:
        parsed = parse_txn_ref(txn_ref)
        if parsed:
            oid, pid = parsed
            payment = Payment.objects.filter(id=pid, order_id=oid).first()
    if not payment:
        return '01', 'Payment not found'

    response_code = (params.get('vnp_ResponseCode') or '').strip()
    trans_status = (params.get('vnp_TransactionStatus') or '').strip()
    success = response_code == '00' and (not trans_status or trans_status == '00')

    if not success:
        return '00', 'Acknowledged (no capture)'

    if payment.status == Payment.Status.COMPLETED:
        return '00', 'Confirm Success'

    base = _order_base()
    try:
        r = requests.get(
            f'{base}/api/v1/orders/{payment.order_id}/',
            params={'user_id': payment.user_id},
            timeout=15,
        )
    except requests.RequestException:
        return '99', 'Order service unreachable'

    if r.status_code != 200:
        return '01', 'Order not found'

    try:
        order = r.json()
    except Exception:
        return '01', 'Invalid order response'

    if order.get('status') == 'paid':
        _sync_payment_completed(payment.id)
        return '00', 'Confirm Success'

    amount_raw = (params.get('vnp_Amount') or '0').strip()
    try:
        vnp_amount = int(amount_raw)
    except ValueError:
        return '04', 'Invalid amount'

    expected = _amount_cents_vnd(order.get('total'))
    if vnp_amount != expected:
        return '04', 'Amount mismatch'

    try:
        pr = requests.post(
            f'{base}/api/v1/orders/{payment.order_id}/pay/',
            json={'user_id': payment.user_id},
            timeout=30,
        )
    except requests.RequestException:
        return '99', 'Order pay unreachable'

    if pr.status_code >= 400:
        try:
            body = pr.json()
            detail = body.get('detail', str(body))
        except Exception:
            detail = pr.text
        if pr.status_code == 400 and 'not awaiting' in str(detail).lower():
            _sync_payment_completed(payment.id)
            return '00', 'Confirm Success'
        return '99', f'Pay failed: {detail}'

    _sync_payment_completed(payment.id)
    return '00', 'Confirm Success'
