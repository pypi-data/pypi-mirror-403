"""SENTD API client implementation."""

from typing import Any, Dict, List, Optional, Union

import httpx

from sentd.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SentdError,
    ValidationError,
)
from sentd.types import (
    Analytics,
    BatchSendOptions,
    BatchSendResult,
    CreateTemplateOptions,
    CreateWebhookOptions,
    Domain,
    Email,
    SendEmailOptions,
    SendEmailResponse,
    Template,
    Webhook,
)


class BaseAPI:
    """Base class for API resources."""

    def __init__(self, client: "Sentd") -> None:
        self._client = client


class EmailsAPI(BaseAPI):
    """API for managing emails."""

    def send(
        self,
        *,
        from_address: str,
        to: Union[str, List[str]],
        subject: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        routing: Optional[Dict[str, Any]] = None,
        tracking: Optional[Dict[str, Any]] = None,
        send_at: Optional[str] = None,
        send_at_timezone: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Send an email.

        Args:
            from_address: Sender email address
            to: Recipient email address(es)
            subject: Email subject (required unless using template)
            html: HTML body content
            text: Plain text body content
            reply_to: Reply-to email address
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            template_id: Template ID to use
            template_data: Variables for template rendering
            attachments: List of attachments
            metadata: Custom metadata
            routing: Routing configuration
            tracking: Tracking configuration
            send_at: ISO 8601 datetime for scheduled sending
            send_at_timezone: IANA timezone for send_at

        Returns:
            SendEmailResponse with email ID and status
        """
        payload: Dict[str, Any] = {
            "from": from_address,
            "to": to,
        }

        if subject:
            payload["subject"] = subject
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if reply_to:
            payload["replyTo"] = reply_to
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        if template_id:
            payload["template_id"] = template_id
        if template_data:
            payload["template_data"] = template_data
        if attachments:
            payload["attachments"] = attachments
        if metadata:
            payload["metadata"] = metadata
        if routing:
            payload["routing"] = routing
        if tracking:
            payload["tracking"] = tracking
        if send_at:
            payload["send_at"] = send_at
        if send_at_timezone:
            payload["send_at_timezone"] = send_at_timezone

        response = self._client._request("POST", "/api/send", json=payload)
        return SendEmailResponse(**response)

    def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List emails.

        Args:
            limit: Maximum number of emails to return
            offset: Offset for pagination
            status: Filter by status
            from_date: Filter by start date
            to_date: Filter by end date

        Returns:
            Dict with emails list and pagination info
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        return self._client._request("GET", "/api/emails", params=params)

    def get(self, email_id: str) -> Email:
        """
        Get email details.

        Args:
            email_id: ID of the email

        Returns:
            Email object
        """
        response = self._client._request("GET", f"/api/emails/{email_id}")
        return Email(**response["data"])

    def cancel(self, email_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled email.

        Args:
            email_id: ID of the scheduled email

        Returns:
            Cancellation result
        """
        return self._client._request("DELETE", f"/api/emails/{email_id}")

    def reschedule(
        self,
        email_id: str,
        send_at: str,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reschedule an email.

        Args:
            email_id: ID of the email
            send_at: New ISO 8601 datetime
            timezone: IANA timezone

        Returns:
            Updated email data
        """
        payload: Dict[str, Any] = {"send_at": send_at}
        if timezone:
            payload["send_at_timezone"] = timezone

        return self._client._request("PATCH", f"/api/emails/{email_id}", json=payload)


class BatchAPI(BaseAPI):
    """API for batch email operations."""

    def send(
        self,
        *,
        emails: List[Dict[str, Any]],
        from_address: Optional[str] = None,
        subject: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        template_id: Optional[str] = None,
        tracking: Optional[Dict[str, Any]] = None,
        routing: Optional[Dict[str, Any]] = None,
    ) -> BatchSendResult:
        """
        Send batch emails with personalization.

        Args:
            emails: List of email recipients with individual data
            from_address: Sender email address
            subject: Email subject template
            html: HTML body template
            text: Plain text body template
            template_id: Template ID to use
            tracking: Tracking configuration
            routing: Routing configuration

        Returns:
            BatchSendResult with sent/failed counts
        """
        payload: Dict[str, Any] = {"emails": emails}

        if from_address:
            payload["from"] = from_address
        if subject:
            payload["subject"] = subject
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if template_id:
            payload["templateId"] = template_id
        if tracking:
            payload["tracking"] = tracking
        if routing:
            payload["routing"] = routing

        response = self._client._request("POST", "/api/batch", json=payload)
        return BatchSendResult(**response["data"])


class TemplatesAPI(BaseAPI):
    """API for managing email templates."""

    def list(self) -> List[Template]:
        """
        List all templates.

        Returns:
            List of Template objects
        """
        response = self._client._request("GET", "/api/templates")
        return [Template(**t) for t in response["data"]["templates"]]

    def create(
        self,
        *,
        name: str,
        slug: str,
        subject_template: str,
        html_template: Optional[str] = None,
        text_template: Optional[str] = None,
        variables: Optional[List[str]] = None,
        default_from: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Template:
        """
        Create a new template.

        Args:
            name: Template name
            slug: URL-safe identifier
            subject_template: Subject with {{variables}}
            html_template: HTML body with {{variables}}
            text_template: Plain text body with {{variables}}
            variables: List of variable names
            default_from: Default sender address
            reply_to: Default reply-to address

        Returns:
            Created Template object
        """
        payload: Dict[str, Any] = {
            "name": name,
            "slug": slug,
            "subject_template": subject_template,
        }

        if html_template:
            payload["html_template"] = html_template
        if text_template:
            payload["text_template"] = text_template
        if variables:
            payload["variables"] = variables
        if default_from:
            payload["default_from"] = default_from
        if reply_to:
            payload["reply_to"] = reply_to

        response = self._client._request("POST", "/api/templates", json=payload)
        return Template(**response["data"]["template"])

    def get(self, template_id: str) -> Template:
        """
        Get template details.

        Args:
            template_id: ID of the template

        Returns:
            Template object
        """
        response = self._client._request("GET", f"/api/templates/{template_id}")
        return Template(**response["data"]["template"])

    def update(self, template_id: str, **kwargs: Any) -> Template:
        """
        Update a template.

        Args:
            template_id: ID of the template
            **kwargs: Fields to update

        Returns:
            Updated Template object
        """
        response = self._client._request("PATCH", f"/api/templates/{template_id}", json=kwargs)
        return Template(**response["data"]["template"])

    def delete(self, template_id: str) -> Dict[str, Any]:
        """
        Delete a template.

        Args:
            template_id: ID of the template

        Returns:
            Deletion result
        """
        return self._client._request("DELETE", f"/api/templates/{template_id}")

    def preview(
        self,
        template_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Preview a template with sample data.

        Args:
            template_id: ID of the template
            data: Variables for rendering

        Returns:
            Rendered subject, html, and text
        """
        payload = {"data": data or {}}
        return self._client._request(
            "POST", f"/api/templates/{template_id}/preview", json=payload
        )

    def duplicate(self, template_id: str) -> Template:
        """
        Duplicate a template.

        Args:
            template_id: ID of the template to duplicate

        Returns:
            New Template object
        """
        response = self._client._request("POST", f"/api/templates/{template_id}/duplicate")
        return Template(**response["data"]["template"])


class DomainsAPI(BaseAPI):
    """API for managing verified domains."""

    def list(self) -> List[Domain]:
        """
        List all domains.

        Returns:
            List of Domain objects
        """
        response = self._client._request("GET", "/api/domains")
        return [Domain(**d) for d in response["data"]["domains"]]

    def add(self, domain: str) -> Domain:
        """
        Add a domain for verification.

        Args:
            domain: Domain name to verify

        Returns:
            Domain object with DNS records
        """
        response = self._client._request("POST", "/api/domains", json={"domain": domain})
        return Domain(**response["data"])

    def verify(self, domain_id: str) -> Domain:
        """
        Verify a domain's DNS records.

        Args:
            domain_id: ID of the domain

        Returns:
            Updated Domain object
        """
        response = self._client._request("POST", f"/api/domains/{domain_id}/verify")
        return Domain(**response["data"])

    def delete(self, domain_id: str) -> Dict[str, Any]:
        """
        Delete a domain.

        Args:
            domain_id: ID of the domain

        Returns:
            Deletion result
        """
        return self._client._request("DELETE", f"/api/domains/{domain_id}")


class WebhooksAPI(BaseAPI):
    """API for managing webhook endpoints."""

    def list(self) -> List[Webhook]:
        """
        List all webhooks.

        Returns:
            List of Webhook objects
        """
        response = self._client._request("GET", "/api/webhooks-config")
        return [Webhook(**w) for w in response["data"]["webhooks"]]

    def create(
        self,
        url: str,
        events: List[str],
        enabled: bool = True,
    ) -> Webhook:
        """
        Create a webhook endpoint.

        Args:
            url: Webhook URL
            events: List of event types to subscribe
            enabled: Whether webhook is active

        Returns:
            Webhook object with secret
        """
        payload = {"url": url, "events": events, "enabled": enabled}
        response = self._client._request("POST", "/api/webhooks-config", json=payload)
        return Webhook(**response["data"]["webhook"])

    def get(self, webhook_id: str) -> Webhook:
        """
        Get webhook details.

        Args:
            webhook_id: ID of the webhook

        Returns:
            Webhook object
        """
        response = self._client._request("GET", f"/api/webhooks-config/{webhook_id}")
        return Webhook(**response["data"]["webhook"])

    def update(self, webhook_id: str, **kwargs: Any) -> Webhook:
        """
        Update a webhook.

        Args:
            webhook_id: ID of the webhook
            **kwargs: Fields to update

        Returns:
            Updated Webhook object
        """
        response = self._client._request(
            "PATCH", f"/api/webhooks-config/{webhook_id}", json=kwargs
        )
        return Webhook(**response["data"]["webhook"])

    def delete(self, webhook_id: str) -> Dict[str, Any]:
        """
        Delete a webhook.

        Args:
            webhook_id: ID of the webhook

        Returns:
            Deletion result
        """
        return self._client._request("DELETE", f"/api/webhooks-config/{webhook_id}")

    def test(self, webhook_id: str) -> Dict[str, Any]:
        """
        Send a test event to webhook.

        Args:
            webhook_id: ID of the webhook

        Returns:
            Test result
        """
        return self._client._request("POST", f"/api/webhooks-config/{webhook_id}/test")


class AnalyticsAPI(BaseAPI):
    """API for accessing analytics."""

    def get(
        self,
        days: int = 30,
        group_by: Optional[str] = None,
    ) -> Analytics:
        """
        Get analytics data.

        Args:
            days: Number of days to include
            group_by: Grouping period (day, week, month)

        Returns:
            Analytics object
        """
        params: Dict[str, Any] = {"days": days}
        if group_by:
            params["groupBy"] = group_by

        response = self._client._request("GET", "/api/analytics", params=params)
        return Analytics(**response["data"])

    def export_csv(self, days: int = 30) -> str:
        """
        Export analytics as CSV.

        Args:
            days: Number of days to include

        Returns:
            CSV string
        """
        response = self._client._request(
            "GET", "/api/analytics/export", params={"days": days, "format": "csv"}
        )
        return response.get("csv", "")


class Sentd:
    """
    SENTD API client.

    Example:
        >>> client = Sentd("your_api_key")
        >>> result = client.emails.send(
        ...     from_address="hello@yourdomain.com",
        ...     to="user@example.com",
        ...     subject="Welcome!",
        ...     html="<h1>Hello World</h1>"
        ... )
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.sentd.io",
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the SENTD client.

        Args:
            api_key: Your SENTD API key
            base_url: API base URL (default: https://api.sentd.io)
            timeout: Request timeout in seconds (default: 30)
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

        self._http_client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "sentd-python/1.0.0",
            },
        )

        # Initialize API resources
        self.emails = EmailsAPI(self)
        self.batch = BatchAPI(self)
        self.templates = TemplatesAPI(self)
        self.domains = DomainsAPI(self)
        self.webhooks = WebhooksAPI(self)
        self.analytics = AnalyticsAPI(self)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        try:
            response = self._http_client.request(
                method,
                path,
                params=params,
                json=json,
            )

            if response.status_code == 401:
                raise AuthenticationError()

            if response.status_code == 404:
                data = response.json()
                raise NotFoundError(data.get("error", "Resource not found"))

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    retry_after=int(retry_after) if retry_after else None
                )

            if response.status_code >= 400:
                data = response.json()
                if response.status_code == 400:
                    raise ValidationError(
                        data.get("error", "Validation error"),
                        details=data.get("details"),
                    )
                raise SentdError(
                    data.get("error", "Unknown error"),
                    status_code=response.status_code,
                    details=data.get("details"),
                )

            return response.json()

        except httpx.RequestError as e:
            raise SentdError(f"Request failed: {e}")

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()

    def __enter__(self) -> "Sentd":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
