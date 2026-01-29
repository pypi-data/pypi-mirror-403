"""Notification Protocol - Core interface for sending notifications.

This module defines the NotificationProtocol for sending various
types of notifications: email, SMS, push notifications, in-app alerts.

Supports template-based notifications and multiple channels.
"""

from enum import StrEnum
from typing import Any, Protocol


class NotificationType(StrEnum):
    """Types of notifications."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationProtocol(Protocol):
    """Protocol defining the contract for notification services.

    This is the primary port for sending notifications in the hexagonal
    architecture. Implementations handle different delivery channels.

    Implementations include:
    - SMTPNotificationAdapter: Email via SMTP
    - TwilioAdapter: SMS via Twilio
    - FCMAdapter: Push notifications via Firebase

    Example usage:
        notifier: NotificationProtocol = container.get(NotificationProtocol)

        await notifier.send_email(
            to=["user@example.com"],
            subject="Welcome!",
            body="<h1>Welcome to the platform</h1>",
            template="welcome",
            context={"user_name": "John"}
        )
    """

    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        template: str | None = None,
        context: dict[str, Any] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[tuple[str, bytes]] | None = None,
    ) -> bool:
        """Send an email notification.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body (HTML or plain text)
            template: Optional template name for rendering
            context: Template context variables
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            attachments: List of (filename, content) tuples

        Returns:
            True if sent successfully
        """
        ...

    async def send_sms(
        self,
        to: str,
        body: str,
        *,
        template: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Send an SMS notification.

        Args:
            to: Phone number in E.164 format
            body: SMS message body
            template: Optional template name
            context: Template context variables

        Returns:
            True if sent successfully
        """
        ...

    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send a push notification.

        Args:
            user_id: Target user's ID
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            True if sent successfully
        """
        ...

    async def send_in_app(
        self,
        user_id: str,
        title: str,
        body: str,
        *,
        link: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send an in-app notification.

        Stored in database and shown in the UI notification center.

        Args:
            user_id: Target user's ID
            title: Notification title
            body: Notification body
            link: Optional link to navigate to
            data: Optional custom data payload

        Returns:
            True if created successfully
        """
        ...


__all__ = [
    "NotificationProtocol",
    "NotificationType",
]
