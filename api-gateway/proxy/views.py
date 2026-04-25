import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Define the service mapping
SERVICES = {
    'customers': 'http://customer-service:8000',
    'products': 'http://product-service:8001',
    'ai': 'http://ai-service:8002',
    'cart': 'http://cart-service:8004',
}

@csrf_exempt
def proxy_view(request, service_name, path):
    if service_name not in SERVICES:
        return JsonResponse({'error': 'Service not found'}, status=404)
        
    target_url = f"{SERVICES[service_name]}/{path}"
    
    # Handle query params
    if request.META['QUERY_STRING']:
        target_url += f"?{request.META['QUERY_STRING']}"

    # Prepare headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}

    try:
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, stream=True)
        elif request.method == 'POST':
            response = requests.post(target_url, headers=headers, data=request.body, stream=True)
        elif request.method == 'PUT':
            response = requests.put(target_url, headers=headers, data=request.body, stream=True)
        elif request.method == 'PATCH':
            response = requests.patch(target_url, headers=headers, data=request.body, stream=True)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, headers=headers, stream=True)
        else:
            return JsonResponse({'error': 'Method not supported'}, status=405)

        # Create response
        proxy_response = HttpResponse(
            response.raw,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )
        
        # Pass headers back
        for key, value in response.headers.items():
            if key.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                proxy_response[key] = value
                
        return proxy_response
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Service unreachable: {str(e)}'}, status=502)
