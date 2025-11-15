# SendBaba Python SDK

Official Python client for the SendBaba API.

## Installation
```bash
pip install sendbaba
```

## Quick Start
```python
from sendbaba import SendBaba

# Initialize client
client = SendBaba(api_key="sb_live_your_api_key")

# Send an email
response = client.send_email(
    to="user@example.com",
    subject="Welcome to SendBaba!",
    html="<h1>Hello!</h1><p>Welcome to our platform.</p>"
)

print(f"Email queued: {response['data']['id']}")
```

## Usage Examples

### Send Email
```python
# Simple email
client.send_email(
    to="user@example.com",
    subject="Hello",
    html="<h1>Hello World!</h1>"
)

# With all options
client.send_email(
    to="user@example.com",
    from_email="noreply@yourdomain.com",
    subject="Order Confirmation",
    html="<h1>Your order is confirmed!</h1>",
    text="Your order is confirmed!",
    reply_to="support@yourdomain.com",
    priority=8,
    tags=["order", "confirmation"]
)
```

### Manage Contacts
```python
# Create contact
contact = client.create_contact(
    email="john@example.com",
    first_name="John",
    last_name="Doe",
    company="Acme Inc",
    tags=["customer", "premium"],
    custom_fields={"plan": "premium"}
)

# Get contact
contact = client.get_contact(contact_id="xxx")

# Update contact
client.update_contact(
    contact_id="xxx",
    first_name="Jane",
    tags=["vip"]
)

# List contacts
contacts = client.list_contacts(status="active", limit=100)
```

### Campaigns
```python
# Create campaign
campaign = client.create_campaign(
    name="Welcome Series",
    subject="Welcome!",
    from_email="marketing@yourdomain.com"
)

# Get campaign
campaign = client.get_campaign(campaign_id="xxx")

# List campaigns
campaigns = client.list_campaigns()
```

## Error Handling
```python
from sendbaba import SendBaba
from sendbaba.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError
)

client = SendBaba(api_key="your_key")

try:
    client.send_email(
        to="invalid-email",
        subject="Test"
    )
except ValidationError as e:
    print(f"Validation error: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

## Documentation

Full API documentation: https://sendbaba.com/api/docs

## Support

- Email: support@sendbaba.com
- Docs: https://sendbaba.com/docs
- GitHub: https://github.com/sendbaba/sendbaba-python
