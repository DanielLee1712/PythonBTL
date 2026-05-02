import os

import requests
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .services.vnpay import build_vnpay_payment_url, vnpay_configured
from .services.vnpay_complete import try_complete_vnpay_payment
from .services.vnpay_verify import merge_vnp_params

DEFAULT_VNPAY_BRAND_IMG = 'https://sandbox.vnpayment.vn/paymentv2/images/branding.png'


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()[:45]
    return (request.META.get('REMOTE_ADDR') or '127.0.0.1')[:45]


class PaymentInitView(APIView):
    """Create or reuse a pending payment; optionally build signed VNPAY redirect URL."""

    def post(self, request):
        order_id = request.data.get('order_id')
        user_id = request.data.get('user_id')
        if order_id is None or user_id is None:
            return Response(
                {'detail': 'order_id and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order_id = int(order_id)
        user_id = int(user_id)

        base = os.environ.get('ORDER_SERVICE_BASE_URL', 'http://127.0.0.1:8005').rstrip('/')
        try:
            r = requests.get(
                f'{base}/api/v1/orders/{order_id}/',
                params={'user_id': user_id},
                timeout=15,
            )
        except requests.RequestException as e:
            return Response(
                {'detail': 'Order service unreachable', 'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if r.status_code == 404:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = {'detail': r.text}
            return Response(body, status=r.status_code)

        order = r.json()
        if order.get('status') != 'pending_payment':
            return Response(
                {'detail': 'Order is not pending payment'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.filter(
            order_id=order_id,
            status=Payment.Status.PENDING,
        ).first()
        if not payment:
            payment = Payment.objects.create(order_id=order_id, user_id=user_id)

        payload = {
            'id': payment.id,
            'order_id': payment.order_id,
            'user_id': payment.user_id,
            'status': payment.status,
            'vnpay_qr_url': DEFAULT_VNPAY_BRAND_IMG,
            'vnpay_payment_url': None,
            'vnpay_live': False,
        }

        if vnpay_configured():
            try:
                pay_url, txn_ref = build_vnpay_payment_url(
                    order_id=order_id,
                    payment_id=payment.id,
                    order_total=order.get('total'),
                    order_info=f'Thanh toan don hang #{order_id}',
                    client_ip=_client_ip(request),
                )
            except (KeyError, ValueError) as exc:
                return Response(
                    {'detail': f'VNPAY URL build failed: {exc}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if payment.vnp_txn_ref != txn_ref:
                payment.vnp_txn_ref = txn_ref
                payment.save(update_fields=['vnp_txn_ref'])
            payload['vnpay_payment_url'] = pay_url
            payload['vnpay_live'] = True

        return Response(payload)


class PaymentConfirmView(APIView):
    """Complete mock payment: mark order paid via order-service."""

    def post(self, request, payment_id):
        user_id = request.data.get('user_id') or request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        user_id = int(user_id)

        try:
            payment = Payment.objects.get(id=payment_id, user_id=user_id)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status != Payment.Status.PENDING:
            return Response(
                {'detail': 'Payment is not pending'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base = os.environ.get('ORDER_SERVICE_BASE_URL', 'http://127.0.0.1:8005').rstrip('/')
        try:
            r = requests.post(
                f'{base}/api/v1/orders/{payment.order_id}/pay/',
                json={'user_id': user_id},
                timeout=30,
            )
        except requests.RequestException as e:
            return Response(
                {'detail': 'Order service unreachable', 'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = {'detail': r.text}
            return Response(body, status=r.status_code)

        payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=['status'])

        try:
            order_payload = r.json()
        except Exception:
            order_payload = {}

        return Response(
            {
                'payment_status': payment.status,
                'order': order_payload,
            }
        )


@method_decorator(csrf_exempt, name='dispatch')
class VnpayIpnView(View):
    """VNPAY server-to-server IPN (GET/POST). Must be publicly reachable in production."""

    def get(self, request):
        return self._respond(request)

    def post(self, request):
        return self._respond(request)

    def _respond(self, request):
        params = merge_vnp_params(request)
        code, msg = try_complete_vnpay_payment(params)
        return JsonResponse({'RspCode': code, 'Message': msg})


@method_decorator(csrf_exempt, name='dispatch')
class VnpayReturnView(View):
    """
    Browser return from VNPAY: verify signature, mark paid, redirect to frontend.
    Set VNPAY_RETURN_URL to this path on the API gateway.
    """

    def get(self, request):
        params = merge_vnp_params(request)
        code, msg = try_complete_vnpay_payment(params)
        fe_base = os.environ.get('VNPAY_FRONTEND_URL', 'http://localhost:5173/').rstrip('/')
        vnp_rc = (params.get('vnp_ResponseCode') or '').strip()
        if vnp_rc == '00' and code == '00':
            return HttpResponseRedirect(f'{fe_base}/?paid=1')
        return HttpResponseRedirect(f'{fe_base}/?payment_failed=1')
