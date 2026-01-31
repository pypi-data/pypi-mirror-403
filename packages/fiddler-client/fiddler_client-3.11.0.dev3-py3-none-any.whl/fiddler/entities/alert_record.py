"""Alert Record entity for tracking triggered alerts and monitoring history.

The AlertRecord entity represents individual instances of triggered alerts from
AlertRules. Alert records provide detailed information about when alerts fired,
what values triggered them, and their severity levels. They are essential for
alert analysis, debugging monitoring issues, and understanding system behavior.

Key Concepts:
    **Alert Lifecycle**:
        - **Trigger**: Alert rule evaluates metric and finds threshold violation
        - **Record Creation**: AlertRecord is created with trigger details
        - **Notification**: Notifications are sent based on severity and configuration

    **Severity Levels**:
        - **CRITICAL**: Values exceed critical thresholds, require immediate action
        - **WARNING**: Values exceed warning thresholds, require attention
        - **INFO**: Informational alerts for trend monitoring

    **Alert Context**:
        - **Alert Value**: The actual metric value that triggered the alert
        - **Baseline Value**: The reference value used for comparison (if applicable)
        - **Thresholds**: Warning and critical threshold values at trigger time
        - **Time Buckets**: Time periods for alert evaluation and baseline comparison

    **Alert Analysis**:
        Alert records enable:
        - Historical trend analysis of alert patterns
        - False positive identification and threshold tuning
        - Root cause analysis for model performance issues
        - Compliance reporting and audit trails

Typical Workflow:
    1. AlertRule monitors metric and detects threshold violation
    2. AlertRecord is created with trigger details and context
    3. Notifications are sent to configured channels
    4. Alert records are analyzed for patterns and trends
    5. Thresholds and rules are adjusted based on insights

Example:
    # List recent alert records for a rule
    alert_records = list(AlertRecord.list(
        alert_rule_id=alert_rule.id,
        start_time=datetime.now() - timedelta(days=7)
    ))

    # Analyze alert patterns
    critical_alerts = [r for r in alert_records if r.severity == "CRITICAL"]
    print(f"Critical alerts in last 7 days: {len(critical_alerts)}")

    # Check alert details
    for record in alert_records[:5]:  # Latest 5 alerts
        print(f"Alert: {record.alert_value:.3f} vs threshold {record.critical_threshold:.3f}")
        print(f"Time: {record.created_at}, Feature: {record.feature_name}")
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterator
from uuid import UUID

from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.schemas.alert_record import AlertRecordResp


class AlertRecord(BaseEntity):
    """Alert record representing a triggered alert instance.

    An AlertRecord captures the details of a specific alert trigger event, including
    the metric values, thresholds, and context that caused an AlertRule to fire.
    Alert records provide essential data for monitoring analysis and troubleshooting.

    Attributes:
        alert_run_start_time: Timestamp when the alert evaluation began (Unix timestamp)
        alert_time_bucket: Time bucket identifier for the alert evaluation period
        alert_value: The actual metric value that triggered the alert
        baseline_time_bucket: Time bucket identifier for baseline comparison (if applicable)
        baseline_value: The baseline metric value used for comparison (if applicable)
        is_alert: Boolean indicating if this record represents an active alert
        warning_threshold: Warning threshold value at the time of evaluation
        critical_threshold: Critical threshold value at the time of evaluation
        severity: Alert severity level ("CRITICAL", "WARNING", "INFO")
        failure_reason: Reason for alert evaluation failure (if applicable)
        message: Human-readable alert message with context
        feature_name: Name of the specific feature that triggered the alert (if applicable)
        alert_record_main_version: Major version of the alert record format
        alert_record_sub_version: Minor version of the alert record format
        id: Unique identifier for this alert record
        alert_rule_id: UUID of the :class:`~fiddler.entities.AlertRule` that triggered this alert
        alert_rule_revision: Revision number of the alert rule at trigger time
        created_at: Timestamp when the alert record was created
        updated_at: Timestamp when the alert record was last modified

    Example:
        # List recent critical alerts
        critical_alerts = [
            record for record in AlertRecord.list(
                alert_rule_id=drift_alert.id,
                start_time=datetime.now() - timedelta(days=3)
            )
            if record.severity == "CRITICAL"
        ]

        # Analyze alert details
        for alert in critical_alerts:
            print(f"Alert triggered at {alert.created_at}")
            print(f"Metric value: {alert.alert_value:.3f}")
            print(f"Critical threshold: {alert.critical_threshold:.3f}")
            if alert.feature_name:
                print(f"Feature: {alert.feature_name}")
            print(f"Message: {alert.message}")
            print("---")

        # Check for alert patterns
        hourly_alerts = {}
        for alert in AlertRecord.list(alert_rule_id=perf_alert.id):
            hour = alert.created_at.hour
            hourly_alerts[hour] = hourly_alerts.get(hour, 0) + 1
        print("Alerts by hour:", hourly_alerts)

    Note:
        Alert records are read-only entities created automatically by the Fiddler
        platform when AlertRules trigger. They cannot be created or modified directly
        but provide valuable historical data for analysis and debugging.
    """
    def __init__(self) -> None:
        """Initialize an AlertRecord instance.

        Creates an alert record object for representing triggered alert instances.
        Alert records are typically created automatically by the Fiddler platform
        when AlertRules trigger, rather than being instantiated directly by users.

        Note:
            Alert records are read-only entities that capture historical alert
            trigger events. They are created automatically by the system and
            cannot be modified after creation.
        """

        self.alert_run_start_time: int | None = None
        self.alert_time_bucket: int | None = None
        self.alert_value: float | None = None
        self.baseline_time_bucket: int | None = None
        self.baseline_value: float | None = None
        self.is_alert: bool | None = None
        self.warning_threshold: float | None = None
        self.critical_threshold: float | None = None
        self.severity: str | None = None
        self.failure_reason: str | None = None
        self.message: str | None = None
        self.feature_name: str | None = None
        self.alert_record_main_version: int | None = None
        self.alert_record_sub_version: int | None = None

        self.id: UUID | None = None
        self.alert_rule_id: UUID | None = None
        self.alert_rule_revision: int | None = None
        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        # Deserialized response object
        self._resp: AlertRecordResp | None = None

    @classmethod
    def _from_dict(cls, data: dict) -> AlertRecord:
        """Build alert record object from the given dictionary"""

        # Deserialize the response
        resp_obj = AlertRecordResp(**data)

        # Initialize
        instance = cls()

        # Add remaining fields
        fields = [
            'id',
            'alert_rule_id',
            'alert_rule_revision',
            'alert_run_start_time',
            'alert_time_bucket',
            'alert_value',
            'baseline_time_bucket',
            'baseline_value',
            'is_alert',
            'warning_threshold',
            'critical_threshold',
            'severity',
            'failure_reason',
            'message',
            'feature_name',
            'alert_record_main_version',
            'alert_record_sub_version',
            'created_at',
            'updated_at',
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj

        return instance

    @staticmethod
    def _get_url(alert_rule_id: UUID | str, id_: UUID | str | None = None) -> str:
        """Get alert record resource/item url"""
        url = f'/v2/alert-configs/{alert_rule_id}/records'

        return url if not id_ else f'{url}/{id_}'

    @classmethod
    @handle_api_error
    def list(
        cls,
        alert_rule_id: UUID | str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        ordering: list[str] | None = None,
    ) -> Iterator[AlertRecord]:
        """List alert records triggered by a specific alert rule.

        Retrieves historical alert records for analysis and troubleshooting. This method
        provides access to all alert trigger events within a specified time range,
        enabling pattern analysis and threshold tuning.

        Args:
            alert_rule_id: The unique identifier of the AlertRule to retrieve records for.
                          Must be a valid alert rule UUID.
            start_time: Start time for filtering alert records. If None, defaults to
                       7 days ago. Used to define the beginning of the query window.
            end_time: End time for filtering alert records. If None, defaults to
                     current time. Used to define the end of the query window.
            ordering: List of field names for result ordering. Prefix with "-" for
                     descending order (e.g., ["-created_at"] for newest first).

        Yields:
            :class:`~fiddler.entities.AlertRecord`: Alert record instances with complete
            trigger details and context information.

        Example:
            # Get recent alerts for analysis
            recent_alerts = list(AlertRecord.list(
                alert_rule_id=drift_alert.id,
                start_time=datetime.now() - timedelta(days=3),
                ordering=["-created_at"]  # Newest first
            ))

            # Analyze alert frequency
            print(f"Total alerts in last 3 days: {len(recent_alerts)}")
            critical_count = sum(1 for a in recent_alerts if a.severity == "CRITICAL")
            print(f"Critical alerts: {critical_count}")

            # Check alert patterns by feature
            feature_alerts = {}
            for alert in recent_alerts:
                if alert.feature_name:
                    feature_alerts[alert.feature_name] = feature_alerts.get(alert.feature_name, 0) + 1
            print("Alerts by feature:", feature_alerts)

            # Analyze threshold violations
            for alert in recent_alerts[:5]:  # Latest 5 alerts
                violation_ratio = alert.alert_value / alert.critical_threshold
                print(f"Alert value: {alert.alert_value:.3f} "
                      f"({violation_ratio:.1%} of threshold)")

        Note:
            Results are paginated automatically. The default time range is 7 days
            to balance performance with useful historical context. Use ordering
            parameters to get the most relevant results first.
        """
        params: dict[str, Any] = {
            'start_time': start_time or datetime.now() - timedelta(days=7),
            'end_time': end_time or datetime.now(),
        }
        if ordering:
            params['ordering'] = ordering

        for record in cls._paginate(url=cls._get_url(alert_rule_id), params=params):
            yield cls._from_dict(data=record)
