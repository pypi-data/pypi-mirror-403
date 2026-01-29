# FactPulse SDK Python

Official Python client for the FactPulse API - French electronic invoicing.

## Features

- **Factur-X**: Generation and validation of electronic invoices (MINIMUM, BASIC, EN16931, EXTENDED profiles)
- **Chorus Pro**: Integration with the French public invoicing platform
- **AFNOR PDP/PA**: Submission of flows compliant with XP Z12-013 standard
- **Electronic signature**: PDF signing (PAdES-B-B, PAdES-B-T, PAdES-B-LT)
- **Thin HTTP wrapper**: Generic `post()` and `get()` methods with automatic JWT auth and polling

## Installation

```bash
pip install factpulse
```

## Quick Start

```python
import base64
from factpulse_helpers import FactPulseClient

# Create the client
client = FactPulseClient(
    email="your_email@example.com",
    password="your_password",
    client_uid="your-client-uuid",  # From dashboard: Configuration > Clients
)

# Read your source PDF
with open("source_invoice.pdf", "rb") as f:
    pdf_b64 = base64.b64encode(f.read()).decode()

# Generate Factur-X and submit to PDP in one call
result = client.post(
    "processing/invoices/submit-complete-async",
    invoiceData={
        "number": "INV-2025-001",
        "supplier": {
            "siret": "12345678901234",
            "iban": "FR7630001007941234567890185",
            "routing_address": "12345678901234",
        },
        "recipient": {
            "siret": "98765432109876",
            "routing_address": "98765432109876",
        },
        "lines": [
            {
                "description": "Consulting services",
                "quantity": 10,
                "unitPrice": 100.0,
                "vatRate": 20.0,
            }
        ],
    },
    sourcePdf=pdf_b64,
    profile="EN16931",
    destination={"type": "afnor"},
)

# PDF is in result["content"] (auto-polled, auto-decoded from base64)
with open("facturx_invoice.pdf", "wb") as f:
    f.write(result["content"])

print(f"Flow ID: {result['afnorResult']['flowId']}")
```

## API Methods

The SDK provides two generic methods that map directly to API endpoints:

```python
# POST /api/v1/{path}
result = client.post("path/to/endpoint", key1=value1, key2=value2)

# GET /api/v1/{path}
result = client.get("path/to/endpoint", param1=value1)
```

### Common Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `processing/invoices/submit-complete-async` | POST | Generate Factur-X + submit to PDP |
| `processing/generate-invoice` | POST | Generate Factur-X XML or PDF |
| `processing/validate-xml` | POST | Validate Factur-X XML |
| `processing/validate-facturx-pdf` | POST | Validate Factur-X PDF |
| `processing/sign-pdf` | POST | Sign PDF with certificate |
| `afnor/flow/v1/flows` | POST | Submit flow to AFNOR PDP |
| `afnor/incoming-flows/{flow_id}` | GET | Get incoming invoice |
| `chorus-pro/factures/soumettre` | POST | Submit to Chorus Pro |

## Webhooks

Instead of polling, you can receive results via webhook by adding `callbackUrl`:

```python
# Submit with webhook - returns immediately
result = client.post(
    "processing/invoices/submit-complete-async",
    invoiceData=invoice_data,
    sourcePdf=pdf_b64,
    destination={"type": "afnor"},
    callbackUrl="https://your-server.com/webhook/factpulse",
    webhookMode="INLINE",  # or "DOWNLOAD_URL"
)

task_id = result["taskId"]
# Result will be POSTed to your webhook URL
```

### Webhook Receiver Example (Flask)

```python
import hmac
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)
WEBHOOK_SECRET = "your-shared-secret"

def verify_signature(payload: bytes, signature: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)

@app.route("/webhook/factpulse", methods=["POST"])
def webhook_handler():
    signature = request.headers.get("X-Webhook-Signature", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.json
    event_type = event["event_type"]
    data = event["data"]

    if event_type == "submission.completed":
        flow_id = data.get("afnorResult", {}).get("flowId")
        print(f"Invoice submitted: {flow_id}")
    elif event_type == "submission.failed":
        print(f"Submission failed: {data.get('error')}")

    return jsonify({"status": "received"})
```

### Webhook Event Types

| Event | Description |
|-------|-------------|
| `generation.completed` | Factur-X generated successfully |
| `generation.failed` | Generation failed |
| `validation.completed` | Validation passed |
| `validation.failed` | Validation failed |
| `signature.completed` | PDF signed |
| `submission.completed` | Submitted to PDP/Chorus |
| `submission.failed` | Submission failed |

## Zero-Storage Mode

Pass PDP credentials directly in the request (no server-side storage):

```python
result = client.post(
    "processing/invoices/submit-complete-async",
    invoiceData=invoice_data,
    sourcePdf=pdf_b64,
    destination={
        "type": "afnor",
        "flowServiceUrl": "https://api.pdp.example.com/flow/v1",
        "tokenUrl": "https://auth.pdp.example.com/oauth/token",
        "clientId": "your_pdp_client_id",
        "clientSecret": "your_pdp_client_secret",
    },
)
```

## Error Handling

```python
from factpulse_helpers import FactPulseClient, FactPulseError

try:
    result = client.post("processing/validate-xml", xmlContent=xml_string)
except FactPulseError as e:
    print(f"Error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Details: {e.details}")  # Validation errors list
```

## Resources

- **API Documentation**: https://factpulse.fr/api/facturation/documentation
- **Support**: contact@factpulse.fr

## License

MIT License - Copyright (c) 2025 FactPulse
