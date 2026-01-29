# sentd

Official Python SDK for the [SENTD](https://sentd.io) Email API.

## Installation

```bash
pip install sentd
```

## Quick Start

```python
from sentd import Sentd

client = Sentd("your_api_key")

# Send an email
result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Welcome to SENTD!",
    html="<h1>Hello World</h1>",
)

print(f"Email sent: {result.data.id}")
```

## Configuration

```python
from sentd import Sentd

# Simple configuration with just API key
client = Sentd("your_api_key")

# Advanced configuration
client = Sentd(
    "your_api_key",
    base_url="https://api.sentd.io",  # Optional: custom base URL
    timeout=30.0,  # Optional: request timeout in seconds
)

# Use as context manager for automatic cleanup
with Sentd("your_api_key") as client:
    result = client.emails.send(...)
```

## Sending Emails

### Basic Email

```python
result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Hello!",
    html="<h1>Welcome</h1>",
    text="Welcome",  # Optional plain text fallback
)
```

### With Attachments

```python
import base64

with open("report.pdf", "rb") as f:
    content = base64.b64encode(f.read()).decode()

result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Your Report",
    html="<p>Please find your report attached.</p>",
    attachments=[
        {
            "filename": "report.pdf",
            "content": content,
            "content_type": "application/pdf",
        },
    ],
)
```

### Scheduled Sending

```python
result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Scheduled Email",
    html="<h1>This was scheduled!</h1>",
    send_at="2024-12-25T09:00:00Z",
    send_at_timezone="America/New_York",  # Optional: interpret time in this timezone
)
```

### With Tracking Options

```python
result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Tracked Email",
    html='<h1>Hello</h1><a href="https://example.com">Click here</a>',
    tracking={
        "opens": True,
        "clicks": True,
        "excludeDomains": ["internal.company.com"],
        "excludeUnsubscribe": True,
    },
)
```

### With Routing Options

```python
result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Priority Email",
    html="<h1>Important!</h1>",
    routing={
        "strategy": "reliable",
        "priority": "high",
        "preferredProvider": "ses",
        "allowFallback": True,
    },
)
```

## Batch Sending

Send multiple emails with personalization:

```python
result = client.batch.send(
    from_address="hello@yourdomain.com",
    subject="Hello {{name}}!",
    html="<h1>Hi {{name}}, your order #{{orderId}} is ready!</h1>",
    emails=[
        {"to": "alice@example.com", "data": {"name": "Alice", "orderId": "12345"}},
        {"to": "bob@example.com", "data": {"name": "Bob", "orderId": "67890"}},
    ],
)

print(f"Sent: {result.sent}, Failed: {result.failed}")
```

### Using Templates

```python
result = client.batch.send(
    template_id="order-confirmation",
    emails=[
        {
            "to": "alice@example.com",
            "data": {"name": "Alice", "orderId": "12345", "total": "$99.99"},
        },
        {
            "to": "bob@example.com",
            "data": {"name": "Bob", "orderId": "67890", "total": "$149.99"},
        },
    ],
)
```

## Templates

### Create a Template

```python
template = client.templates.create(
    name="Welcome Email",
    slug="welcome-email",
    subject_template="Welcome to {{company}}!",
    html_template="<h1>Hello {{name}}</h1><p>Thanks for joining {{company}}!</p>",
    variables=["name", "company"],
    default_from="hello@yourdomain.com",
)
```

### Preview a Template

```python
preview = client.templates.preview(
    "template_id",
    data={
        "name": "John",
        "company": "Acme Inc",
    },
)

print(preview["subject"])  # "Welcome to Acme Inc!"
print(preview["html"])  # "<h1>Hello John</h1>..."
```

### Send with Template

```python
result = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    template_id="template_id",
    template_data={
        "name": "John",
        "company": "Acme Inc",
    },
)
```

## Managing Emails

### List Emails

```python
response = client.emails.list(
    limit=20,
    status="delivered",
    from_date="2024-01-01",
    to_date="2024-01-31",
)
```

### Get Email Details

```python
email = client.emails.get("email_id")
print(email.status)  # 'delivered'
```

### Cancel Scheduled Email

```python
client.emails.cancel("email_id")
```

### Reschedule Email

```python
client.emails.reschedule(
    "email_id",
    send_at="2024-12-26T09:00:00Z",
    timezone="America/New_York",
)
```

## Domains

### Add a Domain

```python
domain = client.domains.add("yourdomain.com")

# Get DNS records to configure
for record in domain.dns_records:
    print(f"{record['type']} {record['name']} -> {record['value']}")
```

### Verify Domain

```python
result = client.domains.verify("domain_id")
print(result.verified)  # True or False
```

## Webhooks

### Create a Webhook

```python
webhook = client.webhooks.create(
    url="https://yourapp.com/webhooks/sentd",
    events=["email.delivered", "email.bounced", "email.opened"],
)

# Save the secret for signature verification
print(webhook.secret)
```

### Test Webhook

```python
result = client.webhooks.test("webhook_id")
print(result["success"])  # True if webhook responded OK
```

## Analytics

### Get Analytics

```python
analytics = client.analytics.get(days=30)

print(analytics.summary.open_rate)  # e.g., 45.2
print(analytics.summary.click_rate)  # e.g., 12.8
```

### Export to CSV

```python
csv_data = client.analytics.export_csv(days=30)

with open("analytics.csv", "w") as f:
    f.write(csv_data)
```

## Error Handling

```python
from sentd import (
    Sentd,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    SentdError,
)

client = Sentd("your_api_key")

try:
    client.emails.send(
        from_address="hello@yourdomain.com",
        to="invalid-email",
        subject="Test",
        html="<p>Test</p>",
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limit exceeded, retry after: {e.retry_after}")
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Details: {e.details}")
except NotFoundError as e:
    print(f"Not found: {e.message}")
except SentdError as e:
    print(f"Unknown error: {e}")
```

## Type Hints

This SDK includes full type annotations for all methods and models:

```python
from sentd import Sentd, Email, Template, SendEmailResponse

client = Sentd("your_api_key")

# IDE autocomplete and type checking works
result: SendEmailResponse = client.emails.send(
    from_address="hello@yourdomain.com",
    to="user@example.com",
    subject="Hello",
    html="<p>World</p>",
)

email: Email = client.emails.get(result.data.id)
```

## Requirements

- Python 3.8+
- httpx
- pydantic

## License

MIT
