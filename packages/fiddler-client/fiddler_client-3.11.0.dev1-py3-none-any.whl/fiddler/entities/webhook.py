"""Webhook entity for integrating external notification systems with Fiddler alerts.

The Webhook entity enables integration with external communication platforms like
Slack and Microsoft Teams for alert notifications. Webhooks provide real-time
delivery of alert notifications to team collaboration tools, ensuring that critical
model monitoring alerts reach the right people at the right time.

Key Concepts:
    **Webhook Providers**:
        - **SLACK**: Integration with Slack channels for team notifications
        - **MS_TEAMS**: Integration with Microsoft Teams channels
        - **GENERIC**: Generic HTTP webhooks for custom integrations

    **Notification Flow**:
        1. AlertRule triggers based on threshold violations
        2. Fiddler evaluates notification configuration
        3. Webhook delivers formatted alert message to external system
        4. Team receives real-time notification in their preferred tool

    **Webhook Configuration**:
        - **URL**: The webhook endpoint provided by the external system
        - **Provider**: The type of system (Slack, Teams, etc.)
        - **Format**: Message format is automatically optimized for each provider

    **Security Considerations**:
        - Webhook URLs should be kept secure and not shared publicly
        - Use dedicated channels/teams for ML monitoring alerts
        - Consider rate limiting and message filtering for high-volume alerts

    **Integration Benefits**:
        - Real-time alert delivery to team communication tools
        - Centralized notification management across multiple models
        - Rich message formatting with alert context and severity
        - Integration with existing team workflows and escalation procedures

Typical Workflow:
    1. Create webhook with external system URL and provider type
    2. Configure AlertRules to use the webhook for notifications
    3. Test webhook delivery with sample alerts
    4. Monitor webhook delivery success and adjust as needed
    5. Manage webhook lifecycle (updates, rotation, deletion)

Example:
    # Create Slack webhook for ML team
    slack_webhook = Webhook(
        name="ml-team-alerts",
        url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
        provider=WebhookProvider.SLACK
    ).create()

    # Create Teams webhook for data team
    teams_webhook = Webhook(
        name="data-team-notifications",
        url="https://outlook.office.com/webhook/xxxxx/IncomingWebhook/xxxxx",
        provider=WebhookProvider.MS_TEAMS
    ).create()

    # Configure alert rule to use webhooks
    alert_rule.set_notification_config(
        emails=["ml-team@company.com"],
        webhooks=[slack_webhook.id, teams_webhook.id]
    )
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator
from uuid import UUID

from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule
from fiddler.schemas.webhook import WebhookProvider, WebhookResp
from fiddler.utils.helpers import raise_not_found


class Webhook(BaseEntity):
    """Webhook for integrating external notification systems with Fiddler alerts.

    A Webhook represents an integration endpoint for delivering alert notifications
    to external systems like Slack, Microsoft Teams, or custom HTTP endpoints.
    Webhooks enable real-time alert delivery to team communication tools.

    Attributes:
        name: Human-readable name for the webhook. Should be descriptive
             and indicate the target system or team.
        url: The webhook endpoint URL provided by the external system.
            This is the destination where alert notifications will be sent.
        provider: The webhook provider type (:class:`~fiddler.schemas.WebhookProvider`).
                 Determines message formatting and delivery method.
        id: Unique identifier assigned after creation
        created_at: Timestamp when the webhook was created
        updated_at: Timestamp when the webhook was last modified

    Example:
        # Create Slack webhook for critical alerts
        slack_webhook = Webhook(
            name="critical-alerts-slack",
            url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            provider=WebhookProvider.SLACK
        ).create()

        # Create Microsoft Teams webhook for team notifications
        teams_webhook = Webhook(
            name="ml-team-notifications",
            url="https://outlook.office.com/webhook/xxxxx/IncomingWebhook/xxxxx",
            provider=WebhookProvider.MS_TEAMS
        ).create()

        # List all webhooks
        webhooks = list(Webhook.list())
        for webhook in webhooks:
            print(f"Webhook: {webhook.name} ({webhook.provider})")

        # Update webhook URL
        webhook = Webhook.from_name("critical-alerts-slack")
        webhook.url = "https://hooks.slack.com/services/NEW/WEBHOOK/URL"
        webhook.update()

    Note:
        Webhook URLs are sensitive credentials that should be kept secure.
        The provider type determines how messages are formatted and delivered.
        Test webhooks thoroughly before using them in production alert rules.
    """
    def __init__(self, name: str, url: str, provider: WebhookProvider | str) -> None:
        """Initialize a Webhook instance.

        Creates a webhook configuration for integrating external notification systems
        with Fiddler alert notifications. The webhook defines where and how alert
        messages should be delivered to external platforms.

        Args:
            name: Human-readable name for the webhook. Should be descriptive and
                 indicate the target system, team, or purpose (e.g., "ml-team-slack",
                 "critical-alerts-teams").
            url: The webhook endpoint URL provided by the external system. This is
                the destination where Fiddler will send HTTP POST requests with
                alert notification payloads.
            provider: The webhook provider type (SLACK, MS_TEAMS, or GENERIC).
                     Determines message formatting, payload structure, and delivery
                     method for optimal integration with the target platform.

        Example:
            # Slack webhook for ML team alerts
            slack_webhook = Webhook(
                name="ml-team-slack-alerts",
                url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
                provider=WebhookProvider.SLACK
            )

            # Microsoft Teams webhook for data quality alerts
            teams_webhook = Webhook(
                name="data-quality-teams",
                url="https://outlook.office.com/webhook/xxxxx/IncomingWebhook/xxxxx",
                provider=WebhookProvider.MS_TEAMS
            )

            # Generic webhook for custom integrations
            custom_webhook = Webhook(
                name="custom-monitoring-system",
                url="https://monitoring.company.com/webhooks/fiddler",
                provider=WebhookProvider.GENERIC
            )

        Note:
            After initialization, call create() to register the webhook with the
            Fiddler platform. Webhook URLs are sensitive and should be kept secure.
        """
        self.name = name
        self.url = url
        # provider is 'SLACK', 'MS_TEAMS' as of May 2025.
        self.provider = provider

        self.id: UUID | None = None
        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        # Deserialized response object
        self._resp: WebhookResp | None = None

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get webhook resource/item url"""
        url = '/v2/webhooks'
        return url if not id_ else f'{url}/{id_}'

    @classmethod
    def _from_dict(cls, data: dict) -> Webhook:
        """Build entity object from the given dictionary"""

        # Deserialize the response
        resp_obj = WebhookResp(**data)

        # Initialize
        instance = cls(name=resp_obj.name, url=resp_obj.url, provider=resp_obj.provider)
        # Add remaining fields
        fields = ['id', 'created_at', 'updated_at']
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj
        return instance

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = WebhookResp(**data)

        fields = [
            'id',
            'name',
            'url',
            'provider',
            'created_at',
            'updated_at',
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> Webhook:
        """
        Get the webhook instance using webhook id

        :params uuid: UUID belongs to the Webhook
        :returns: `Webhook` object
        """
        response = cls._client().get(url=cls._get_url(id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def from_name(cls, name: str) -> Webhook:
        """Get the webhook instance using webhook name"""
        _filter = QueryCondition(
            rules=[QueryRule(field='name', operator=OperatorType.EQUAL, value=name)]
        )

        response = cls._client().get(
            url=cls._get_url(), params={'filter': _filter.json()}
        )
        if response.json()['data']['total'] == 0:
            raise_not_found('Webhook not found for the given identifier')

        return cls._from_dict(data=response.json()['data']['items'][0])

    @classmethod
    @handle_api_error
    def list(cls) -> Iterator[Webhook]:
        """Get a list of all webhooks in the organization"""
        for webhook in cls._paginate(url=cls._get_url()):
            yield cls._from_dict(data=webhook)

    @handle_api_error
    def create(self) -> Webhook:
        """
        Create a new webhook

        :params name: name of webhook
        :params url: webhook url
        :params provider: Either 'SLACK' or 'MS_TEAMS'

        :returns: Created `Webhook` object.
        """

        request_body = {
            'name': self.name,
            'url': self.url,
            'provider': self.provider,
        }
        response = self._client().post(
            url=self._get_url(),
            # Use custom JSON encoder (for UUID etc)
            data=request_body,
            headers={'Content-Type': 'application/json'},
        )
        self._refresh_from_response(response=response)
        return self

    @handle_api_error
    def update(self) -> None:
        """Update an existing webhook."""
        body: dict[str, Any] = {
            'name': self.name,
            'url': self.url,
            'provider': self.provider,
        }

        response = self._client().patch(url=self._get_url(id_=self.id), data=body)
        self._refresh_from_response(response=response)

    @handle_api_error
    def delete(self) -> None:
        """Delete an existing webhook."""

        self._client().delete(url=self._get_url(id_=self.id))
