# HookPulse Python SDK

[![PyPI version](https://badge.fury.io/py/hookpulse.svg)](https://badge.fury.io/py/hookpulse)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [HookPulse](https://hookpulse.io) - the enterprise-grade serverless task scheduling and webhook orchestration platform. Built with Elixir/OTP for 99.9% uptime.

## Installation

```bash
pip install hookpulse
```

## Quick Start

```python
from hookpulse import HookPulseClient

# Initialize the client
client = HookPulseClient(
    api_key="your-api-key",
    brand_uuid="your-brand-uuid"
)

# Create an interval schedule (every hour)
schedule = client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="interval",
    interval_seconds=3600
)

# Create a cron schedule (daily at 9 AM)
schedule = client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="cron",
    cron_expression="0 9 * * *",
    timezone="America/New_York"
)
```

## Configuration

### Default Configuration

By default, the SDK uses `https://api.hookpulse.io` as the base URL. You can change this if needed:

```python
client = HookPulseClient(
    api_key="your-api-key",
    brand_uuid="your-brand-uuid",
    base_url="https://custom-api.example.com"  # Optional
)
```

### Authentication

The SDK requires two authentication headers:
- `x-hookpulse-api-key`: Your API key (get from dashboard → API Keys)
- `x-brand-uuid`: Your brand UUID (get from dashboard after adding a brand)

Both are automatically included in all requests.

## Features

### Schedule Management

#### Interval Schedules
```python
# Schedule every 5 minutes
client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="interval",
    interval_seconds=300
)

# Schedule every 2 hours
client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="interval",
    interval_seconds=7200
)
```

#### Cron Schedules
```python
# Daily at 9 AM
client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="cron",
    cron_expression="0 9 * * *",
    timezone="America/New_York"
)

# Every Monday at 8 AM
client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="cron",
    cron_expression="0 8 * * 1",
    timezone="UTC"
)
```

#### Clocked Schedules (One-time)
```python
from datetime import datetime

# Schedule for a specific date/time
client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="clocked",
    scheduled_time="2024-12-25T09:00:00Z",
    timezone="UTC"
)
```

#### Solar Schedules
```python
# Trigger at sunrise
client.create_schedule(
    webhook_url="https://example.com/webhook",
    schedule_type="solar",
    solar_event="sunrise",
    latitude=40.7128,
    longitude=-74.0060,
    timezone="America/New_York"
)
```

### Webhook Templates

```python
# Create a webhook template
template = client.create_webhook_template(
    name="Payment Notification",
    url="https://api.example.com/payments",
    method="POST",
    headers={"Authorization": "Bearer {{ #api_key }}"},
    body={"amount": "{{ amount }}", "currency": "USD"}
)

# Get all templates
templates = client.get_webhook_templates(page=1)

# Update a template
client.update_webhook_template(
    template_uuid=template["data"]["uuid"],
    name="Updated Payment Notification"
)

# Delete a template
client.delete_webhook_template(template_uuid=template["data"]["uuid"])
```

### Workflow Templates

```python
# Create a workflow template
workflow = client.create_workflow_template(
    name="Payment Processing",
    mode="fifo",  # or "concurrent"
    steps=[
        {
            "name": "Validate Payment",
            "type": "webhook",
            "url": "https://api.example.com/validate",
            "method": "POST"
        },
        {
            "name": "Process Payment",
            "type": "webhook",
            "url": "https://api.example.com/process",
            "method": "POST",
            "condition": {
                "field": "{{ step.validate.response.status }}",
                "operator": "eq",
                "value": "valid"
            }
        }
    ]
)
```

### Schedule Management

```python
# Get all schedules
schedules = client.get_schedules(page=1, status="active")

# Get a specific schedule
schedule = client.get_schedule(schedule_uuid="uuid-here")

# Update a schedule
client.update_schedule(
    schedule_uuid="uuid-here",
    webhook_url="https://new-url.com/webhook"
)

# Pause a schedule
client.update_schedule_status("uuid-here", "paused")

# Resume a schedule
client.update_schedule_status("uuid-here", "active")

# Delete a schedule
client.delete_schedule("uuid-here")
```

### System Secrets

```python
# Create a secret
secret = client.create_secret(
    key="api_key",
    value="secret-value-123"
)

# Get all secrets
secrets = client.get_secrets(page=1)

# Update a secret
client.update_secret(
    secret_uuid=secret["data"]["uuid"],
    value="new-secret-value"
)

# Delete a secret
client.delete_secret(secret_uuid=secret["data"]["uuid"])
```

### Human Approvals

```python
# Approve a workflow execution
client.approve_execution(execution_plan_uuid="uuid-here")

# Reject a workflow execution
client.reject_execution(execution_plan_uuid="uuid-here")
```

### Timezones

```python
# Get all supported timezones
timezones = client.get_timezones()
```

## Error Handling

```python
from hookpulse import HookPulseClient, HookPulseError, HookPulseAPIError, HookPulseAuthError

try:
    client = HookPulseClient(api_key="invalid", brand_uuid="invalid")
    schedule = client.create_schedule(...)
except HookPulseAuthError as e:
    print(f"Authentication failed: {e}")
except HookPulseAPIError as e:
    print(f"API error ({e.status_code}): {e}")
except HookPulseError as e:
    print(f"Error: {e}")
```

## Advanced Usage

### Custom Base URL

```python
# Use a custom API endpoint
client = HookPulseClient(
    api_key="your-api-key",
    brand_uuid="your-brand-uuid",
    base_url="https://custom-api.example.com"
)
```

### Request Timeout

```python
# Set custom timeout (default: 30 seconds)
client = HookPulseClient(
    api_key="your-api-key",
    brand_uuid="your-brand-uuid",
    timeout=60
)
```

## Documentation

- [Full API Documentation](https://docs.hookpulse.io/docs)
- [HookPulse Website](https://hookpulse.io)
- [OpenAPI Specification](https://api.hookpulse.io/openapi.json)

## Requirements

- Python 3.7+
- requests >= 2.25.0

## License

MIT License - see LICENSE file for details

## Support

- Email: care@hookpulse.io
- Documentation: https://docs.hookpulse.io/docs
- Issues: https://github.com/hookpulse/hookpulse-python/issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
