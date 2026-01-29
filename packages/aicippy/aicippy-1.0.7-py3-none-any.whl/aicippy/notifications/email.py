"""
Email notifications for AiCippy via AWS SES.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import boto3
from botocore.config import Config

from aicippy.config import get_settings
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import async_retry

logger = get_logger(__name__)


class EmailTemplate(str, Enum):
    """Available email templates."""

    LOGIN_ALERT = "aicippy-login-alert"
    USAGE_REPORT = "aicippy-usage-report"
    ERROR_NOTIFICATION = "aicippy-error-notification"


@dataclass
class EmailMessage:
    """Email message structure."""

    to: list[str]
    subject: str
    html_body: str
    text_body: str
    reply_to: str | None = None


class EmailSender:
    """
    Email sender using AWS SES.

    Supports both templated and raw emails.
    """

    def __init__(self) -> None:
        """Initialize email sender."""
        self._settings = get_settings()
        self._client = None

    def _get_client(self):
        """Get or create SES client."""
        if self._client is None:
            config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
            self._client = boto3.client(
                "ses",
                region_name=self._settings.aws_region,
                config=config,
            )
        return self._client

    @async_retry(max_attempts=3, min_wait=1.0)
    async def send_templated_email(
        self,
        template: EmailTemplate,
        to: str | list[str],
        template_data: dict[str, Any],
    ) -> bool:
        """
        Send a templated email.

        Args:
            template: Email template to use.
            to: Recipient email(s).
            template_data: Data for template variables.

        Returns:
            True if sent successfully.
        """
        import json

        recipients = [to] if isinstance(to, str) else to
        client = self._get_client()

        loop = asyncio.get_event_loop()

        try:
            await loop.run_in_executor(
                None,
                lambda: client.send_templated_email(
                    Source=self._settings.ses_verified_email,
                    Destination={"ToAddresses": recipients},
                    Template=template.value,
                    TemplateData=json.dumps(template_data),
                ),
            )

            logger.info(
                "templated_email_sent",
                template=template.value,
                recipients=len(recipients),
            )
            return True

        except Exception as e:
            logger.error(
                "templated_email_failed",
                template=template.value,
                error=str(e),
            )
            raise

    @async_retry(max_attempts=3, min_wait=1.0)
    async def send_raw_email(self, message: EmailMessage) -> bool:
        """
        Send a raw email.

        Args:
            message: Email message to send.

        Returns:
            True if sent successfully.
        """
        client = self._get_client()

        loop = asyncio.get_event_loop()

        try:
            await loop.run_in_executor(
                None,
                lambda: client.send_email(
                    Source=self._settings.ses_verified_email,
                    Destination={"ToAddresses": message.to},
                    Message={
                        "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                        "Body": {
                            "Text": {"Data": message.text_body, "Charset": "UTF-8"},
                            "Html": {"Data": message.html_body, "Charset": "UTF-8"},
                        },
                    },
                    ReplyToAddresses=[message.reply_to] if message.reply_to else [],
                ),
            )

            logger.info(
                "raw_email_sent",
                recipients=len(message.to),
                subject=message.subject[:50],
            )
            return True

        except Exception as e:
            logger.error(
                "raw_email_failed",
                error=str(e),
            )
            raise

    async def send_login_alert(
        self,
        user_email: str,
        login_time: datetime,
        device_info: str,
        location: str,
    ) -> bool:
        """
        Send login alert email.

        Args:
            user_email: User's email address.
            login_time: Time of login.
            device_info: Device information.
            location: Login location.

        Returns:
            True if sent successfully.
        """
        return await self.send_templated_email(
            EmailTemplate.LOGIN_ALERT,
            user_email,
            {
                "login_time": login_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "device_info": device_info,
                "location": location,
            },
        )

    async def send_usage_report(
        self,
        total_tokens: int,
        sessions_count: int,
        agents_used: int,
        period_start: datetime,
        period_end: datetime,
        models: list[dict[str, Any]],
    ) -> bool:
        """
        Send usage report email.

        Args:
            total_tokens: Total tokens used.
            sessions_count: Number of sessions.
            agents_used: Number of agents used.
            period_start: Report period start.
            period_end: Report period end.
            models: Per-model usage breakdown.

        Returns:
            True if sent successfully.
        """
        return await self.send_templated_email(
            EmailTemplate.USAGE_REPORT,
            self._settings.admin_email,
            {
                "total_tokens": f"{total_tokens:,}",
                "sessions_count": str(sessions_count),
                "agents_used": str(agents_used),
                "period_start": period_start.strftime("%Y-%m-%d %H:%M UTC"),
                "period_end": period_end.strftime("%Y-%m-%d %H:%M UTC"),
                "models": models,
            },
        )

    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        service: str,
        request_id: str,
        stack_trace: str,
    ) -> bool:
        """
        Send error notification email.

        Args:
            error_type: Type of error.
            error_message: Error message.
            service: Service that errored.
            request_id: Request/correlation ID.
            stack_trace: Stack trace.

        Returns:
            True if sent successfully.
        """
        return await self.send_templated_email(
            EmailTemplate.ERROR_NOTIFICATION,
            self._settings.admin_email,
            {
                "error_type": error_type,
                "error_message": error_message,
                "error_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "service": service,
                "request_id": request_id,
                "stack_trace": stack_trace,
            },
        )
