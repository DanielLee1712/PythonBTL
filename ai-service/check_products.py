import urllib.request, json

url = 'http://product-service:8001/api/v1/products/?page_size=100'
req = urllib.request.Request(url, headers={'Accept': 'application/json'})
with urllib.request.urlopen(req, timeout=5) as resp:
    raw = resp.read().decode('utf-8')
payload = json.loads(raw)
results = payload.get('results', payload)

# Count by category
cats = {}
for p in results:
    cat = p.get('category_name') or 'None'
    title = p.get('title') or p.get('name') or '(no title)'
    pid = p.get('id')
    if cat not in cats:
        cats[cat] = []
    cats[cat].append((pid, title))

for cat, items in sorted(cats.items()):
    print(f'\n=== Category: {cat} ({len(items)} products) ===')
    for pid, title in items[:5]:
        print(f'  ID {pid}: {title}')
    if len(items) > 5:
        print(f'  ... and {len(items)-5} more')
