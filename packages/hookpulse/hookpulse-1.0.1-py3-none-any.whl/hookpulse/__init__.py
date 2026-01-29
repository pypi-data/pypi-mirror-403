"""
HookPulse Python SDK

Official Python client library for HookPulse API - the enterprise-grade serverless 
task scheduling and webhook orchestration platform.

Example:
    >>> from hookpulse import HookPulseClient
    >>> client = HookPulseClient(
    ...     api_key="your-api-key",
    ...     brand_uuid="your-brand-uuid"
    ... )
    >>> # Create a schedule
    >>> schedule = client.create_schedule({
    ...     "webhook_url": "https://example.com/webhook",
    ...     "schedule_type": "interval",
    ...     "interval_seconds": 3600
    ... })
"""

from .client import HookPulseClient
from .exceptions import HookPulseError, HookPulseAPIError, HookPulseAuthError

__version__ = "1.0.1"
__all__ = ["HookPulseClient", "HookPulseError", "HookPulseAPIError", "HookPulseAuthError"]
