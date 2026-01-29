"""
SENTD Python SDK

Official Python client for the SENTD Email API.

Example:
    >>> from sentd import Sentd
    >>> client = Sentd("your_api_key")
    >>> result = client.emails.send(
    ...     from_address="hello@yourdomain.com",
    ...     to="user@example.com",
    ...     subject="Welcome!",
    ...     html="<h1>Hello World</h1>"
    ... )
    >>> print(result.data.id)
"""

from sentd.client import Sentd
from sentd.types import (
    Attachment,
    RoutingOptions,
    TrackingOptions,
    SendEmailOptions,
    SendEmailResponse,
    Email,
    Template,
    Domain,
    Webhook,
    Analytics,
)
from sentd.exceptions import (
    SentdError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
)

__version__ = "1.0.0"
__all__ = [
    "Sentd",
    "Attachment",
    "RoutingOptions",
    "TrackingOptions",
    "SendEmailOptions",
    "SendEmailResponse",
    "Email",
    "Template",
    "Domain",
    "Webhook",
    "Analytics",
    "SentdError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
]
