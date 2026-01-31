# Pincho Python Library

Official Python client for [Pincho](https://pincho.dev) push notifications.

## Installation

```bash
pip install pincho-sdk
```

## Quick Start

```python
from pincho import Pincho

# Auto-load token from PINCHO_TOKEN env var
with Pincho() as client:
    client.send('Deploy Complete', 'Version 1.2.3 deployed')

# Or provide token explicitly
with Pincho(token='YOUR_TOKEN') as client:
    client.send('Alert', 'Server CPU at 95%')
```

## Features

```python
# Full parameters
client.send(
    title='Deploy Complete',
    message='Version 1.2.3 deployed',
    type='deployment',
    tags=['production', 'backend'],
    image_url='https://example.com/success.png',
    action_url='https://example.com/deploy/123'
)

# AI-powered notifications (NotifAI)
response = client.notifai('deployment finished, v2.1.3 is live')
print(response.notification)  # AI-generated title, message, tags

# Encrypted messages
client.send(
    title='Security Alert',
    message='Sensitive data',
    type='security',
    encryption_password='your_password'
)

# Async support
from pincho import AsyncPincho

async with AsyncPincho() as client:
    await client.send('Test', 'Message')
```

## Configuration

```python
# Environment variables (recommended)
# PINCHO_TOKEN - API token (required if not passed to constructor)
# PINCHO_TIMEOUT - Request timeout in seconds (default: 30)
# PINCHO_MAX_RETRIES - Retry attempts (default: 3)

# Or explicit configuration
client = Pincho(
    token='abc12345',
    timeout=60.0,
    max_retries=5
)
```

## Error Handling

```python
from pincho import (
    Pincho,
    AuthenticationError,
    ValidationError,
    RateLimitError
)

try:
    with Pincho() as client:
        client.send('Title', 'Message')
except AuthenticationError:
    print("Invalid token")
except ValidationError:
    print("Invalid parameters")
except RateLimitError:
    print("Rate limited - auto-retry handled this")
```

Automatic retry with exponential backoff for network errors, 5xx, and 429 (rate limit).

## Smart Rate Limiting

The library automatically handles rate limits with Retry-After header support:

```python
with Pincho() as client:
    client.send('Alert', 'Message')

    # Check rate limit status after any request
    if client.last_rate_limit:
        print(f"Remaining: {client.last_rate_limit.remaining}/{client.last_rate_limit.limit}")
        print(f"Resets at: {client.last_rate_limit.reset}")
```

See [Advanced Documentation](docs/ADVANCED.md) for detailed rate limit monitoring patterns.

## Links

- **Get Token**: App → Settings → Help → copy token
- **Documentation**: https://pincho.dev/help
- **Repository**: https://gitlab.com/pincho/pincho-python
- **PyPI**: https://pypi.org/project/pincho/

## License

MIT
