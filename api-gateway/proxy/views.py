import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import jwt

# Define the service mapping
SERVICES = {
    'customers': 'http://customer-service:8000',
    'products': 'http://product-service:8001',
    'ai': 'http://ai-service:8002',
    'cart': 'http://cart-service:8004',
    'order': 'http://order-service:8005',
    'payment': 'http://payment-service:8006',
    'shipping': 'http://shipping-service:8007',
}

def _require_staff(request):
    auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION") or ""
    if not auth.lower().startswith("bearer "):
        return False, JsonResponse({"detail": "Missing Bearer token"}, status=401)
    token = auth.split(" ", 1)[1].strip()
    key = os.environ.get("JWT_SIGNING_KEY") or ""
    if not key:
        return False, JsonResponse({"detail": "JWT_SIGNING_KEY not configured"}, status=500)
    try:
        payload = jwt.decode(token, key, algorithms=["HS256"])
    except Exception:
        return False, JsonResponse({"detail": "Invalid token"}, status=401)
    if not (payload.get("is_staff") or payload.get("is_admin")):
        return False, JsonResponse({"detail": "Forbidden"}, status=403)
    return True, None

@csrf_exempt
def proxy_view(request, service_name, path):
    if service_name not in SERVICES:
        return JsonResponse({'error': 'Service not found'}, status=404)

    # Staff-only endpoints (enforced at gateway)
    # - Stock adjustment
    # - Product CRUD (write methods)
    if service_name == "products":
        p = str(path)
        is_adjust_stock = p.startswith("api/v1/products/adjust-stock/")
        is_product_write = p.startswith("api/v1/products/") and request.method in ("POST", "PUT", "PATCH", "DELETE")
        if is_adjust_stock or is_product_write:
            ok, resp = _require_staff(request)
            if not ok:
                return resp
        
    target_url = f"{SERVICES[service_name]}/{path}"
    
    # Handle query params
    if request.META['QUERY_STRING']:
        target_url += f"?{request.META['QUERY_STRING']}"

    # Prepare headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}

    # Never follow redirects: e.g. VNPAY return → 302 to frontend URL would run inside this container
    # (localhost:5173 is unreachable from Docker), breaking browser redirects.
    req_kw = {
        'headers': headers,
        'timeout': 120,
        'allow_redirects': False,
    }
    try:
        if request.method == 'GET':
            response = requests.get(target_url, **req_kw)
        elif request.method == 'POST':
            response = requests.post(target_url, data=request.body, **req_kw)
        elif request.method == 'PUT':
            response = requests.put(target_url, data=request.body, **req_kw)
        elif request.method == 'PATCH':
            response = requests.patch(target_url, data=request.body, **req_kw)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, **req_kw)
        else:
            return JsonResponse({'error': 'Method not supported'}, status=405)

        proxy_response = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type') or 'application/json',
        )
        
        skip_headers = {
            'content-encoding',
            'transfer-encoding',
            'connection',
            'content-length',
        }
        for key, value in response.headers.items():
            if key.lower() not in skip_headers:
                proxy_response[key] = value
                
        return proxy_response
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Service unreachable: {str(e)}'}, status=502)
