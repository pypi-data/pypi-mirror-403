"""Type definitions for the SENTD SDK using Pydantic."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, EmailStr, Field


# Enums
RoutingStrategy = Literal["cheapest", "fastest", "reliable", "round-robin", "priority", "specific"]
Provider = Literal["resend", "sendgrid", "ses"]
Priority = Literal["critical", "high", "normal", "low", "bulk"]
EmailStatus = Literal["queued", "scheduled", "sent", "delivered", "bounced", "failed", "complained"]


class Attachment(BaseModel):
    """Email attachment."""

    filename: str = Field(..., min_length=1, description="Name of the file")
    content: str = Field(..., min_length=1, description="Base64-encoded file content")
    content_type: Optional[str] = Field(None, description="MIME type of the file")
    cid: Optional[str] = Field(None, description="Content-ID for inline images")
    disposition: Optional[Literal["attachment", "inline"]] = Field(
        "attachment", description="How the attachment is displayed"
    )


class RoutingOptions(BaseModel):
    """Email routing configuration."""

    strategy: Optional[RoutingStrategy] = Field(None, description="Routing strategy")
    preferred_provider: Optional[Provider] = Field(None, alias="preferredProvider")
    priority: Optional[Priority] = None
    allow_fallback: Optional[bool] = Field(True, alias="allowFallback")


class TrackingOptions(BaseModel):
    """Email tracking configuration."""

    opens: bool = Field(True, description="Track email opens")
    clicks: bool = Field(True, description="Track link clicks")
    exclude_domains: Optional[List[str]] = Field(
        None, alias="excludeDomains", description="Domains to exclude from tracking"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None, alias="excludePatterns", description="URL patterns to exclude"
    )
    exclude_unsubscribe: bool = Field(
        True, alias="excludeUnsubscribe", description="Exclude unsubscribe links"
    )


class SendEmailOptions(BaseModel):
    """Options for sending an email."""

    from_address: str = Field(..., alias="from", description="Sender email address")
    to: Union[str, List[str]] = Field(..., description="Recipient email(s)")
    subject: Optional[str] = Field(None, max_length=998)
    html: Optional[str] = None
    text: Optional[str] = None
    reply_to: Optional[str] = Field(None, alias="replyTo")
    cc: Optional[Union[str, List[str]]] = None
    bcc: Optional[Union[str, List[str]]] = None
    template_id: Optional[str] = Field(None, alias="templateId")
    template_data: Optional[Dict[str, Any]] = Field(None, alias="templateData")
    attachments: Optional[List[Attachment]] = None
    metadata: Optional[Dict[str, Any]] = None
    routing: Optional[RoutingOptions] = None
    tracking: Optional[TrackingOptions] = None
    send_at: Optional[str] = Field(None, alias="sendAt", description="ISO 8601 datetime")
    send_at_timezone: Optional[str] = Field(
        None, alias="sendAtTimezone", description="IANA timezone"
    )

    class Config:
        populate_by_name = True


class SendEmailData(BaseModel):
    """Response data for a sent email."""

    id: str
    message_id: Optional[str] = Field(None, alias="messageId")
    status: EmailStatus
    provider: Optional[str] = None
    scheduled_at: Optional[str] = Field(None, alias="scheduledAt")
    scheduled_timezone: Optional[str] = Field(None, alias="scheduledTimezone")
    routing: Optional[Dict[str, Any]] = None


class SendEmailResponse(BaseModel):
    """Response from sending an email."""

    success: bool
    data: Optional[SendEmailData] = None
    error: Optional[str] = None
    details: Optional[Any] = None


class Email(BaseModel):
    """Email record."""

    id: str
    from_address: str = Field(..., alias="fromAddress")
    to_addresses: List[str] = Field(..., alias="toAddresses")
    cc_addresses: Optional[List[str]] = Field(None, alias="ccAddresses")
    bcc_addresses: Optional[List[str]] = Field(None, alias="bccAddresses")
    subject: str
    status: EmailStatus
    provider: Optional[str] = None
    provider_message_id: Optional[str] = Field(None, alias="providerMessageId")
    open_count: int = Field(0, alias="openCount")
    click_count: int = Field(0, alias="clickCount")
    created_at: datetime = Field(..., alias="createdAt")
    sent_at: Optional[datetime] = Field(None, alias="sentAt")
    delivered_at: Optional[datetime] = Field(None, alias="deliveredAt")


class Template(BaseModel):
    """Email template."""

    id: str
    name: str
    slug: str
    subject_template: str = Field(..., alias="subjectTemplate")
    html_template: Optional[str] = Field(None, alias="htmlTemplate")
    text_template: Optional[str] = Field(None, alias="textTemplate")
    variables: List[str] = Field(default_factory=list)
    default_from: Optional[str] = Field(None, alias="defaultFrom")
    reply_to: Optional[str] = Field(None, alias="replyTo")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class CreateTemplateOptions(BaseModel):
    """Options for creating a template."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    subject_template: str = Field(..., alias="subjectTemplate", min_length=1, max_length=998)
    html_template: Optional[str] = Field(None, alias="htmlTemplate")
    text_template: Optional[str] = Field(None, alias="textTemplate")
    variables: Optional[List[str]] = None
    default_from: Optional[str] = Field(None, alias="defaultFrom")
    reply_to: Optional[str] = Field(None, alias="replyTo")


class Domain(BaseModel):
    """Verified domain."""

    id: str
    domain: str
    verified: bool
    dns_records: Optional[List[Dict[str, str]]] = Field(None, alias="dnsRecords")
    created_at: datetime = Field(..., alias="createdAt")
    verified_at: Optional[datetime] = Field(None, alias="verifiedAt")


class Webhook(BaseModel):
    """Webhook endpoint."""

    id: str
    url: str
    events: List[str]
    enabled: bool = True
    secret: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")


class CreateWebhookOptions(BaseModel):
    """Options for creating a webhook."""

    url: str
    events: List[str]
    enabled: bool = True


class AnalyticsSummary(BaseModel):
    """Analytics summary statistics."""

    total_emails: int = Field(..., alias="totalEmails")
    total_opens: int = Field(..., alias="totalOpens")
    total_clicks: int = Field(..., alias="totalClicks")
    unique_opens: int = Field(..., alias="uniqueOpens")
    unique_clicks: int = Field(..., alias="uniqueClicks")
    open_rate: float = Field(..., alias="openRate")
    click_rate: float = Field(..., alias="clickRate")


class DailyStats(BaseModel):
    """Daily analytics breakdown."""

    date: str
    sent: int
    delivered: int
    opened: int
    clicked: int


class Analytics(BaseModel):
    """Analytics data."""

    period: Dict[str, Any]
    summary: AnalyticsSummary
    by_status: Dict[str, int] = Field(..., alias="byStatus")
    daily: List[DailyStats]
    top_emails: List[Dict[str, Any]] = Field(..., alias="topEmails")
    devices: Dict[str, int]
    clients: Dict[str, int]


class BatchEmailItem(BaseModel):
    """Individual email in a batch request."""

    to: str
    data: Optional[Dict[str, Any]] = None
    send_at: Optional[str] = Field(None, alias="sendAt")


class BatchSendOptions(BaseModel):
    """Options for sending batch emails."""

    from_address: Optional[str] = Field(None, alias="from")
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    template_id: Optional[str] = Field(None, alias="templateId")
    emails: List[BatchEmailItem]
    tracking: Optional[TrackingOptions] = None
    routing: Optional[RoutingOptions] = None


class BatchSendResult(BaseModel):
    """Result of a batch send operation."""

    sent: int
    failed: int
    results: List[Dict[str, Any]]
