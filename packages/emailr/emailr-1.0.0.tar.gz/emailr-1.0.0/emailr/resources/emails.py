"""
Email resource for sending and managing emails.
"""

from typing import Any, Dict, List, Optional, Union

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    CreateForwardingRuleRequest,
    Email,
    ForwardEmailRequest,
    ForwardingRule,
    ListEmailsParams,
    PaginatedResponse,
    Pagination,
    SendEmailRequest,
    SendEmailResponse,
    SuccessResponse,
)


class EmailsResource:
    """Synchronous email resource for sending and managing emails."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(
        self,
        to: Union[str, List[str]],
        *,
        from_: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Send an email to one or multiple recipients.

        Args:
            to: Recipient email address(es)
            from_: Sender email address
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            subject: Email subject
            html: HTML content
            text: Plain text content
            template_id: Template ID to use
            template_data: Data for template variables
            tags: Custom tags for tracking
            scheduled_at: ISO 8601 datetime to schedule sending

        Returns:
            SendEmailResponse with message_id and status
        """
        request = SendEmailRequest(
            to=to,
            from_=from_,
            cc=cc,
            bcc=bcc,
            subject=subject,
            html=html,
            text=text,
            template_id=template_id,
            template_data=template_data,
            tags=tags,
            scheduled_at=scheduled_at,
        )
        data = self._http.post("/v1/emails/send", request.to_dict())
        return SendEmailResponse.from_dict(data)


    def get(self, id: str) -> Email:
        """
        Get email by ID.

        Args:
            id: Email ID

        Returns:
            Email record
        """
        data = self._http.get(f"/v1/emails/{id}")
        return Email.from_dict(data)

    def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> PaginatedResponse[Email]:
        """
        List emails with pagination.

        Args:
            page: Page number
            limit: Number of items per page

        Returns:
            Paginated list of emails
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = self._http.get("/v1/emails", params=params)
        return PaginatedResponse(
            data=[Email.from_dict(e) for e in data["data"]],
            pagination=Pagination(**data["pagination"]),
        )

    def forward(
        self,
        email_id: str,
        to: Union[str, List[str]],
        *,
        message: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Forward an email to other recipients.

        Args:
            email_id: ID of the email to forward
            to: Recipient email address(es)
            message: Optional message to include

        Returns:
            SendEmailResponse with message_id and status
        """
        request = ForwardEmailRequest(email_id=email_id, to=to, message=message)
        data = self._http.post("/v1/emails/forward", request.to_dict())
        return SendEmailResponse.from_dict(data)

    def create_forwarding_rule(
        self,
        name: str,
        from_pattern: str,
        to_addresses: List[str],
        *,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Create an email forwarding rule.

        Args:
            name: Rule name
            from_pattern: Pattern to match sender
            to_addresses: Addresses to forward to
            active: Whether the rule is active

        Returns:
            Dict with id and success status
        """
        request = CreateForwardingRuleRequest(
            name=name,
            from_pattern=from_pattern,
            to_addresses=to_addresses,
            active=active,
        )
        return self._http.post("/v1/emails/forwarding-rules", request.to_dict())

    def list_forwarding_rules(self) -> List[ForwardingRule]:
        """
        List all forwarding rules.

        Returns:
            List of forwarding rules
        """
        data = self._http.get("/v1/emails/forwarding-rules")
        return [ForwardingRule.from_dict(r) for r in data["data"]]

    def delete_forwarding_rule(self, id: str) -> SuccessResponse:
        """
        Delete a forwarding rule.

        Args:
            id: Forwarding rule ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/emails/forwarding-rules/{id}")
        return SuccessResponse(success=data.get("success", True))


class AsyncEmailsResource:
    """Asynchronous email resource for sending and managing emails."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def send(
        self,
        to: Union[str, List[str]],
        *,
        from_: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Send an email to one or multiple recipients.

        Args:
            to: Recipient email address(es)
            from_: Sender email address
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            subject: Email subject
            html: HTML content
            text: Plain text content
            template_id: Template ID to use
            template_data: Data for template variables
            tags: Custom tags for tracking
            scheduled_at: ISO 8601 datetime to schedule sending

        Returns:
            SendEmailResponse with message_id and status
        """
        request = SendEmailRequest(
            to=to,
            from_=from_,
            cc=cc,
            bcc=bcc,
            subject=subject,
            html=html,
            text=text,
            template_id=template_id,
            template_data=template_data,
            tags=tags,
            scheduled_at=scheduled_at,
        )
        data = await self._http.post("/v1/emails/send", request.to_dict())
        return SendEmailResponse.from_dict(data)

    async def get(self, id: str) -> Email:
        """Get email by ID."""
        data = await self._http.get(f"/v1/emails/{id}")
        return Email.from_dict(data)

    async def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> PaginatedResponse[Email]:
        """List emails with pagination."""
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = await self._http.get("/v1/emails", params=params)
        return PaginatedResponse(
            data=[Email.from_dict(e) for e in data["data"]],
            pagination=Pagination(**data["pagination"]),
        )

    async def forward(
        self,
        email_id: str,
        to: Union[str, List[str]],
        *,
        message: Optional[str] = None,
    ) -> SendEmailResponse:
        """Forward an email to other recipients."""
        request = ForwardEmailRequest(email_id=email_id, to=to, message=message)
        data = await self._http.post("/v1/emails/forward", request.to_dict())
        return SendEmailResponse.from_dict(data)

    async def create_forwarding_rule(
        self,
        name: str,
        from_pattern: str,
        to_addresses: List[str],
        *,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Create an email forwarding rule."""
        request = CreateForwardingRuleRequest(
            name=name,
            from_pattern=from_pattern,
            to_addresses=to_addresses,
            active=active,
        )
        return await self._http.post("/v1/emails/forwarding-rules", request.to_dict())

    async def list_forwarding_rules(self) -> List[ForwardingRule]:
        """List all forwarding rules."""
        data = await self._http.get("/v1/emails/forwarding-rules")
        return [ForwardingRule.from_dict(r) for r in data["data"]]

    async def delete_forwarding_rule(self, id: str) -> SuccessResponse:
        """Delete a forwarding rule."""
        data = await self._http.delete(f"/v1/emails/forwarding-rules/{id}")
        return SuccessResponse(success=data.get("success", True))
