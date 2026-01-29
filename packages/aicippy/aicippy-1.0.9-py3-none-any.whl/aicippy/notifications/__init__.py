"""
Notifications module for AiCippy.

Provides email notifications via SES for:
- Login alerts
- Usage reports
- Error notifications
"""

from __future__ import annotations

from aicippy.notifications.email import EmailSender, EmailTemplate

__all__ = [
    "EmailSender",
    "EmailTemplate",
]
