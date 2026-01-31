# billingio

Official Python SDK for the [billing.io](https://billing.io) crypto checkout API.

## Installation

```bash
pip install billingio
```

Requires Python 3.9+.

## Quick start

```python
from billingio import BillingIO

client = BillingIO(api_key="sk_test_...")

# Create a checkout
checkout = client.checkouts.create(
    amount_usd=49.99,
    chain="tron",
    token="USDT",
    metadata={"order_id": "ord_12345"},
)

print(checkout.checkout_id)      # co_1a2b3c4d5e
print(checkout.deposit_address)  # blockchain address to send funds to
print(checkout.status)           # "pending"
```

## Resources

The client exposes four resource namespaces that mirror the REST API:

```python
client.checkouts   # create, list, get, get_status
client.webhooks    # create, list, get, delete
client.events      # list, get
client.health      # get
```

### Checkouts

```python
# Create with idempotency key for safe retries
checkout = client.checkouts.create(
    amount_usd=100.00,
    chain="arbitrum",
    token="USDC",
    expires_in_seconds=3600,
    idempotency_key="550e8400-e29b-41d4-a716-446655440000",
)

# List checkouts filtered by status
page = client.checkouts.list(status="confirmed", limit=10)
for co in page.data:
    print(co.checkout_id, co.amount_usd)

# Get a single checkout
checkout = client.checkouts.get("co_1a2b3c4d5e")

# Poll for status (lightweight endpoint)
status = client.checkouts.get_status("co_1a2b3c4d5e")
print(status.confirmations, "/", status.required_confirmations)
```

### Webhook endpoints

```python
# Register an endpoint
endpoint = client.webhooks.create(
    url="https://example.com/webhooks/billing",
    events=["checkout.completed", "checkout.expired"],
    description="Production webhook",
)
# IMPORTANT: store endpoint.secret -- it is only returned once
print(endpoint.secret)  # whsec_...

# List endpoints
page = client.webhooks.list()

# Delete an endpoint
client.webhooks.delete("we_abc123")
```

### Events

```python
# List events for a specific checkout
page = client.events.list(checkout_id="co_1a2b3c4d5e")

# Filter by event type
page = client.events.list(type="checkout.completed")

# Get a single event
event = client.events.get("evt_xyz789")
print(event.type, event.data.status)
```

### Health

```python
health = client.health.get()
print(health.status)   # "healthy"
print(health.version)  # "1.0.0"
```

## Webhook verification

Verify incoming webhook signatures before processing the event. The SDK
ports the exact same HMAC-SHA256 logic used by the billing.io backend.

### Flask example

```python
from flask import Flask, request, abort
from billingio import verify_webhook_signature, WebhookVerificationError

app = Flask(__name__)
WEBHOOK_SECRET = "whsec_..."

@app.route("/webhooks/billing", methods=["POST"])
def handle_webhook():
    raw_body = request.get_data(as_text=True)
    signature = request.headers.get("x-billing-signature", "")

    try:
        event = verify_webhook_signature(raw_body, signature, WEBHOOK_SECRET)
    except WebhookVerificationError:
        abort(400)

    if event["type"] == "checkout.completed":
        checkout_id = event["checkout_id"]
        # Fulfil the order ...

    return "", 200
```

### Django example

```python
import json
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from billingio import verify_webhook_signature, WebhookVerificationError

WEBHOOK_SECRET = "whsec_..."

@csrf_exempt
def billing_webhook(request):
    raw_body = request.body.decode("utf-8")
    signature = request.headers.get("X-Billing-Signature", "")

    try:
        event = verify_webhook_signature(raw_body, signature, WEBHOOK_SECRET)
    except WebhookVerificationError:
        return HttpResponseBadRequest("Invalid signature")

    if event["type"] == "checkout.completed":
        # Fulfil the order ...
        pass

    return HttpResponse(status=200)
```

## Error handling

All API errors are raised as `BillingIOError` with structured fields:

```python
from billingio import BillingIO, BillingIOError

client = BillingIO(api_key="sk_test_...")

try:
    checkout = client.checkouts.get("co_nonexistent")
except BillingIOError as e:
    print(e.type)         # "not_found"
    print(e.code)         # "checkout_not_found"
    print(e.status_code)  # 404
    print(e.message)      # "No checkout found with ID co_nonexistent."
    print(e.param)        # "checkout_id"
```

Error types returned by the API:

| `type`                   | HTTP status | Description                                  |
|--------------------------|-------------|----------------------------------------------|
| `invalid_request`        | 400         | Missing or invalid request parameters        |
| `authentication_error`   | 401         | Invalid or missing API key                   |
| `not_found`              | 404         | Resource does not exist                      |
| `idempotency_conflict`   | 409         | Idempotency key reused with different params |
| `rate_limited`           | 429         | Too many requests                            |
| `internal_error`         | 500         | Unexpected server error                      |

## Pagination

List endpoints use cursor-based pagination. You can page manually or use
the `auto_paginate` helper to iterate through all items:

### Manual pagination

```python
cursor = None
while True:
    page = client.checkouts.list(cursor=cursor, limit=50)
    for checkout in page.data:
        process(checkout)
    if not page.has_more:
        break
    cursor = page.next_cursor
```

### auto_paginate helper

```python
from billingio import auto_paginate

for checkout in auto_paginate(client.checkouts.list, status="confirmed"):
    print(checkout.checkout_id)
```

`auto_paginate` accepts the same keyword arguments as the underlying
`list()` method and yields individual items across all pages.

## Configuration

| Parameter   | Default                          | Description                   |
|-------------|----------------------------------|-------------------------------|
| `api_key`   | *(required)*                     | Your secret API key           |
| `base_url`  | `https://api.billing.io/v1`      | API base URL override         |

```python
# Point to a local development server
client = BillingIO(
    api_key="sk_test_...",
    base_url="http://localhost:8080/v1",
)
```

## License

Proprietary -- see [billing.io/terms](https://billing.io/terms).
