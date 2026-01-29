"""Models for notification system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NotificationType(Enum):
    """Types of notification events."""

    BUILD_SUCCESS = "build_success"
    BUILD_FAILURE = "build_failure"
    RELEASE_CREATED = "release_created"
    RELEASE_PUBLISHED = "release_published"
    UPLOAD_SUCCESS = "upload_success"
    UPLOAD_FAILURE = "upload_failure"
    PIPELINE_START = "pipeline_start"
    PIPELINE_SUCCESS = "pipeline_success"
    PIPELINE_FAILURE = "pipeline_failure"
    CUSTOM = "custom"


class ProviderType(Enum):
    """Types of notification providers."""

    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    EMAIL = "email"


@dataclass
class NotificationEvent:
    """Event to be notified about.

    Attributes:
        type: Type of event
        title: Event title
        message: Event message
        status: Success/failure status
        data: Additional event data
        url: Related URL (e.g., release page)
        timestamp: Event timestamp (ISO format)
    """

    type: NotificationType
    title: str
    message: str = ""
    status: str = "info"  # info, success, warning, error
    data: dict[str, Any] = field(default_factory=lambda: {})
    url: str | None = None
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "status": self.status,
            "data": self.data,
            "url": self.url,
            "timestamp": self.timestamp,
        }


@dataclass
class NotificationConfig:
    """Configuration for a notification channel.

    Attributes:
        name: Channel name
        provider: Provider type
        webhook_url: Webhook URL
        enabled: Whether this channel is enabled
        events: Event types to notify (None = all)
        template: Custom message template
        extra: Provider-specific configuration
    """

    name: str
    provider: ProviderType
    webhook_url: str
    enabled: bool = True
    events: list[NotificationType] | None = None
    template: str | None = None
    extra: dict[str, Any] = field(default_factory=lambda: {})

    def should_notify(self, event: NotificationEvent) -> bool:
        """Check if this channel should receive the event."""
        if not self.enabled:
            return False
        if self.events is None:
            return True
        return event.type in self.events

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "provider": self.provider.value,
            "webhook_url": self.webhook_url,
            "enabled": self.enabled,
            "events": [e.value for e in self.events] if self.events else None,
            "template": self.template,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationConfig:
        """Create from dictionary."""
        events = None
        if data.get("events"):
            events = [NotificationType(e) for e in data["events"]]

        return cls(
            name=data["name"],
            provider=ProviderType(data["provider"]),
            webhook_url=data["webhook_url"],
            enabled=data.get("enabled", True),
            events=events,
            template=data.get("template"),
            extra=data.get("extra", {}),
        )


@dataclass
class NotificationResult:
    """Result of sending a notification.

    Attributes:
        config: Channel configuration
        success: Whether notification was sent
        error: Error message if failed
        response_code: HTTP response code
    """

    config: NotificationConfig
    success: bool
    error: str | None = None
    response_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "channel": self.config.name,
            "provider": self.config.provider.value,
            "success": self.success,
        }
        if self.error:
            result["error"] = self.error
        if self.response_code:
            result["response_code"] = self.response_code
        return result
