"""Alert Rule entity for automated monitoring and alerting in ML systems.

The AlertRule entity provides automated monitoring capabilities for ML models by defining
conditions that trigger alerts when specific thresholds are exceeded. Alert rules are
essential for proactive monitoring of model performance, data drift, and operational
issues in production environments.

Key Concepts:
    **Alert Types**:
        - **Drift Alerts**: Detect changes in data distribution or model behavior
        - **Performance Alerts**: Monitor accuracy, precision, recall, and other metrics
        - **Data Quality Alerts**: Track missing values, outliers, and schema changes
        - **Traffic Alerts**: Monitor prediction volume and request patterns

    **Comparison Methods** (:class:`~fiddler.constants.CompareTo`):
        - **BASELINE**: Compare against a fixed baseline dataset
        - **TIME_PERIOD**: Compare against a previous time period
        - **RAW_VALUE**: Compare against absolute threshold values

    **Alert Conditions** (:class:`~fiddler.constants.AlertCondition`):
        - **GT** (Greater Than): Alert when metric exceeds threshold
        - **LT** (Less Than): Alert when metric falls below threshold
        - **OUTSIDE_RANGE**: Alert when metric is outside acceptable range

    **Priority Levels** (:class:`~fiddler.constants.Priority`):
        - **HIGH**: Critical issues requiring immediate attention
        - **MEDIUM**: Important issues requiring timely response
        - **LOW**: Informational alerts for trend monitoring

    **Threshold Types** (:class:`~fiddler.constants.AlertThresholdAlgo`):
        - **MANUAL**: User-defined static thresholds
        - **AUTO**: Automatically calculated dynamic thresholds

    **Bin Sizes** (:class:`~fiddler.constants.BinSize`):
        - **HOUR**: Hourly aggregation for real-time monitoring
        - **DAY**: Daily aggregation for trend analysis
        - **WEEK**: Weekly aggregation for long-term patterns

Typical Workflow:
    1. Define alert rule with metric, thresholds, and conditions
    2. Configure notification channels (email, PagerDuty, webhooks)
    3. Set evaluation frequency and delay parameters
    4. Monitor alerts and adjust thresholds based on feedback
    5. Analyze alert patterns to improve model and data quality

Example:
    # Create drift alert rule
    alert_rule = AlertRule(
        name="feature_drift_alert",
        model_id=model.id,
        metric_id="drift_score",
        priority=Priority.HIGH,
        compare_to=CompareTo.BASELINE,
        condition=AlertCondition.GT,
        bin_size=BinSize.HOUR,
        critical_threshold=0.8,
        warning_threshold=0.6,
        baseline_id=baseline.id
    ).create()

    # Configure notifications
    alert_rule.set_notification_config(
        emails=["ml-team@company.com"],
        pagerduty_services=["ML_ALERTS"]
    )
"""
from __future__ import annotations

import builtins
import json
import logging
from datetime import datetime
from typing import Any, Iterator
from uuid import UUID

from pydantic.v1 import ValidationError

from fiddler.constants.alert_rule import (
    AlertCondition,
    AlertThresholdAlgo,
    BinSize,
    CompareTo,
    Priority,
)
from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.entities.baseline import BaselineCompactMixin
from fiddler.entities.model import ModelCompactMixin
from fiddler.entities.project import ProjectCompactMixin
from fiddler.schemas.alert_rule import AlertRuleResp, NotificationConfig
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule

logger = logging.getLogger(__name__)


class AlertRule(
    BaseEntity, ModelCompactMixin, ProjectCompactMixin, BaselineCompactMixin
):
    """Alert rule for automated monitoring and alerting in ML systems.

    An AlertRule defines conditions that automatically trigger notifications when
    ML model metrics exceed specified thresholds. Alert rules are essential for
    proactive monitoring of model performance, data drift, and operational issues.

    Attributes:
        name: Human-readable name for the alert rule
        model_id: UUID of the associated :class:`~fiddler.entities.Model`
        metric_id: ID of the metric to monitor (drift_score, accuracy, etc.)
        priority: Alert priority level (:class:`~fiddler.constants.Priority`)
        compare_to: Comparison method (:class:`~fiddler.constants.CompareTo`)
        condition: Alert condition (:class:`~fiddler.constants.AlertCondition`)
        bin_size: Time aggregation window (:class:`~fiddler.constants.BinSize`)
        threshold_type: Threshold calculation method (:class:`~fiddler.constants.AlertThresholdAlgo`)
        auto_threshold_params: Parameters for automatic threshold calculation
        critical_threshold: Critical alert threshold value
        warning_threshold: Warning alert threshold value
        columns: List of feature columns to monitor (for feature-specific alerts)
        baseline_id: UUID of reference :class:`~fiddler.entities.Baseline` (if applicable)
        segment_id: UUID of data segment to monitor (if applicable)
        compare_bin_delta: Number of time bins to compare against
        evaluation_delay: Delay in minutes before evaluating alerts
        category: Custom category for organizing alerts
        id: Unique identifier assigned after creation
        project_id: UUID of the containing :class:`~fiddler.entities.Project`
        created_at: Timestamp when alert rule was created
        updated_at: Timestamp when alert rule was last modified

    Example:
        # Create feature drift alert
        drift_alert = AlertRule(
            name="credit_score_drift",
            model_id=model.id,
            metric_id="drift_score",
            priority=Priority.HIGH,
            compare_to=CompareTo.BASELINE,
            condition=AlertCondition.GT,
            bin_size=BinSize.HOUR,
            critical_threshold=0.8,
            warning_threshold=0.6,
            baseline_id=baseline.id,
            columns=["credit_score", "income"]
        ).create()

        # Create performance degradation alert
        perf_alert = AlertRule(
            name="accuracy_drop",
            model_id=model.id,
            metric_id="accuracy",
            priority=Priority.MEDIUM,
            compare_to=CompareTo.TIME_PERIOD,
            condition=AlertCondition.LESSER,
            bin_size=BinSize.DAY,
            critical_threshold=0.85,
            compare_bin_delta=7  # Compare to 7 days ago
        ).create()

        # Configure notifications
        drift_alert.set_notification_config(
            emails=["ml-team@company.com", "data-team@company.com"],
            pagerduty_services=["ML_ALERTS"],
            pagerduty_severity="critical"
        )

    Note:
        Alert rules continuously monitor metrics and trigger notifications when
        thresholds are exceeded. Use appropriate evaluation delays to avoid
        false positives from temporary data fluctuations.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        model_id: UUID | str,
        metric_id: str | UUID,
        priority: Priority | str,
        compare_to: CompareTo | str,
        condition: AlertCondition | str,
        bin_size: BinSize | str,
        threshold_type: AlertThresholdAlgo | str = AlertThresholdAlgo.MANUAL,
        auto_threshold_params: dict[str, Any] | None = None,
        critical_threshold: float | None = None,
        warning_threshold: float | None = None,
        columns: list[str] | None = None,
        baseline_id: UUID | str | None = None,
        segment_id: UUID | str | None = None,
        compare_bin_delta: int | None = None,
        evaluation_delay: int = 0,
        category: str | None = None,
    ) -> None:
        """Initialize an AlertRule instance.

        Creates an alert rule configuration for automated monitoring of ML model metrics.
        The alert rule defines conditions that trigger notifications when thresholds are
        exceeded, enabling proactive monitoring of model performance and data quality.

        Args:
            name: Human-readable name for the alert rule. Should be descriptive
                 and unique within the model context.
            model_id: UUID of the model this alert rule monitors. Must be a valid
                     model that exists in the Fiddler platform.
            metric_id: ID of the metric to monitor (e.g., "drift_score", "accuracy",
                      "precision", "recall", custom metric IDs).
            priority: Alert priority level (HIGH, MEDIUM, LOW). Determines urgency
                     and routing of notifications.
            compare_to: Comparison method for threshold evaluation:
                       - BASELINE: Compare against a fixed baseline
                       - TIME_PERIOD: Compare against previous time period
                       - RAW_VALUE: Compare against absolute threshold
            condition: Alert condition (GT, LT, OUTSIDE_RANGE). Defines when
                      the alert should trigger relative to the threshold.
            bin_size: Time aggregation window (HOUR, DAY, WEEK). Controls how
                     data is grouped for metric calculation.
            threshold_type: Threshold calculation method (MANUAL or AUTO).
                           MANUAL uses user-defined thresholds, AUTO calculates
                           dynamic thresholds based on historical data.
            auto_threshold_params: Parameters for automatic threshold calculation.
                                  Used when threshold_type is AUTO.
            critical_threshold: Critical alert threshold value. Triggers high-priority
                               notifications when exceeded.
            warning_threshold: Warning alert threshold value. Triggers medium-priority
                              notifications when exceeded.
            columns: List of feature columns to monitor. For feature-specific
                    drift alerts. If None, monitors all features.
            baseline_id: UUID of the baseline to compare against. Required when
                        compare_to is BASELINE.
            segment_id: UUID of the data segment to monitor. For segment-specific
                       monitoring (optional).
            compare_bin_delta: Number of time bins to compare against. Used with
                              TIME_PERIOD comparison (e.g., 7 for week-over-week).
            evaluation_delay: Delay in minutes before evaluating alerts. Helps
                             avoid false positives from incomplete data.
            category: Custom category for organizing alerts. Useful for grouping
                     related alerts in dashboards.

        Example:
            # Feature drift alert with baseline comparison
            drift_alert = AlertRule(
                name="income_drift_detection",
                model_id=model.id,
                metric_id="drift_score",
                priority=Priority.HIGH,
                compare_to=CompareTo.BASELINE,
                condition=AlertCondition.GT,
                bin_size=BinSize.HOUR,
                critical_threshold=0.8,
                warning_threshold=0.6,
                baseline_id=baseline.id,
                columns=["income", "credit_score"],
                evaluation_delay=15,  # 15 minute delay
                category="data_quality"
            )

            # Performance monitoring with time comparison
            perf_alert = AlertRule(
                name="weekly_accuracy_check",
                model_id=model.id,
                metric_id="accuracy",
                priority=Priority.MEDIUM,
                compare_to=CompareTo.TIME_PERIOD,
                condition=AlertCondition.LESSER,
                bin_size=BinSize.DAY,
                critical_threshold=0.85,
                compare_bin_delta=7,  # Compare to 7 days ago
                category="performance"
            )

        Note:
            After initialization, call create() to persist the alert rule to the
            Fiddler platform. Alert rules begin monitoring immediately after creation.
        """
        self.name = name
        self.model_id = model_id
        self.metric_id = metric_id
        self.columns = columns
        self.baseline_id = baseline_id
        self.priority = priority
        self.compare_to = compare_to
        self.compare_bin_delta = compare_bin_delta
        self.evaluation_delay = evaluation_delay
        self.threshold_type = threshold_type
        self.auto_threshold_params = auto_threshold_params
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.condition = condition
        self.bin_size = bin_size
        self.segment_id = segment_id
        self.category = category

        self.id: UUID | None = None
        self.project_id: UUID | None = None

        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        # Deserialized response object
        self._resp: AlertRuleResp | None = None

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get alert resource url."""
        url = '/v3/alert-rules'
        return url if not id_ else f'{url}/{id_}'

    @staticmethod
    def _get_notification_url(id_: UUID | str | None = None) -> str:
        """Get alert notification resource url."""
        return f'/v3/alert-rules/{id_}/notification'

    @classmethod
    def _from_dict(cls, data: dict) -> AlertRule:
        """Build entity object from the given dictionary."""

        # Deserialize the response
        resp_obj = AlertRuleResp(**data)

        # Initialize
        instance = cls(
            name=resp_obj.name,
            model_id=resp_obj.model.id,
            metric_id=resp_obj.metric.id,
            priority=resp_obj.priority,
            compare_to=resp_obj.compare_to,
            condition=resp_obj.condition,
            bin_size=resp_obj.bin_size,
            threshold_type=resp_obj.threshold_type,
            auto_threshold_params=resp_obj.auto_threshold_params,
            critical_threshold=resp_obj.critical_threshold,
            warning_threshold=resp_obj.warning_threshold,
            columns=resp_obj.columns,
            baseline_id=resp_obj.baseline.id if resp_obj.baseline else None,
            segment_id=resp_obj.segment.id if resp_obj.segment else None,
            compare_bin_delta=resp_obj.compare_bin_delta,
            evaluation_delay=resp_obj.evaluation_delay,
            category=resp_obj.category,
        )

        # Add remaining fields
        fields = [
            'id',
            'created_at',
            'updated_at',
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance.project_id = resp_obj.project.id
        instance._resp = resp_obj

        return instance

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = AlertRuleResp(**data)

        # Reset properties
        self.model_id = resp_obj.model.id
        self.project_id = resp_obj.project.id
        self.metric_id = resp_obj.metric.id

        # Add remaining fields
        fields = [
            'id',
            'created_at',
            'updated_at',
            'evaluation_delay',
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> AlertRule:
        """Retrieve an alert rule by its unique identifier.

        Fetches an alert rule from the Fiddler platform using its UUID. This method
        returns the complete alert rule configuration including thresholds, notification
        settings, and monitoring status.

        Args:
            id_: The unique identifier (UUID) of the alert rule to retrieve.
                Can be provided as a UUID object or string representation.

        Returns:
            :class:`~fiddler.entities.AlertRule`: The alert rule instance with all
            configuration and metadata populated from the server.

        Raises:
            NotFound: If no alert rule exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Retrieve alert rule by ID
            alert_rule = AlertRule.get(id_="550e8400-e29b-41d4-a716-446655440000")
            print(f"Alert: {alert_rule.name}")
            print(f"Metric: {alert_rule.metric_id}")
            print(f"Priority: {alert_rule.priority}")
            print(f"Critical threshold: {alert_rule.critical_threshold}")

            # Check notification configuration
            notification_config = alert_rule.get_notification_config()
            print(f"Email recipients: {notification_config.emails}")

        Note:
            This method makes an API call to fetch the latest alert rule configuration
            from the server, including any recent threshold or notification updates.
        """

        response = cls._client().get(url=cls._get_url(id_=id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def list(  # pylint: disable=too-many-arguments
        cls,
        model_id: UUID | str,
        metric_id: UUID | str | None = None,
        columns: list[str] | None = None,
        baseline_id: UUID | str | None = None,
        ordering: list[str] | None = None,
    ) -> Iterator[AlertRule]:
        """
        Get a list of all alert rules in the organization.

        :param model_id: list from the specified model
        :param metric_id: list rules set on the specified metric id
        :param columns: list rules set on the specified list of columns
        :param baseline_id: list rules set on the specified baseline_id
        :param ordering: order result as per list of fields. ["-field_name"] for descending

        :return: paginated list of alert rules for the specified filters
        """
        rules: list[QueryRule | QueryCondition] = [
            QueryRule(field='model_id', operator=OperatorType.EQUAL, value=model_id)
        ]

        if baseline_id:
            rules.append(
                QueryRule(
                    field='baseline_id', operator=OperatorType.EQUAL, value=baseline_id
                )
            )
        if metric_id:
            rules.append(
                QueryRule(
                    field='metric_id', operator=OperatorType.EQUAL, value=metric_id
                )
            )
        if columns:
            for column in columns:
                rules.append(
                    QueryRule(
                        field='feature_names', operator=OperatorType.ANY, value=column
                    )
                )

        _filter = QueryCondition(rules=rules)
        params: dict[str, Any] = {'filter': _filter.json()}

        if ordering:
            params['ordering'] = ','.join(ordering)

        for rule in cls._paginate(url=cls._get_url(), params=params):
            yield cls._from_dict(data=rule)

    @handle_api_error
    def delete(self) -> None:
        """Delete an alert rule."""
        assert self.id is not None

        self._client().delete(url=self._get_url(id_=self.id))

    @handle_api_error
    def create(self) -> AlertRule:
        """Create a new alert rule."""
        payload: dict[str, Any] = {
            'name': self.name,
            'model_id': self.model_id,
            'metric_id': self.metric_id,
            'priority': self.priority,
            'compare_to': self.compare_to,
            'condition': self.condition,
            'bin_size': self.bin_size,
            'segment_id': self.segment_id,
            'threshold_type': self.threshold_type,
            'auto_threshold_params': self.auto_threshold_params,
            'critical_threshold': self.critical_threshold,
            'warning_threshold': self.warning_threshold,
            'feature_names': self.columns,
            'compare_bin_delta': self.compare_bin_delta,
            'evaluation_delay': self.evaluation_delay,
            'category': self.category,
        }
        if self.baseline_id:
            payload['baseline_id'] = self.baseline_id

        response = self._client().post(
            url=self._get_url(),
            data=payload,
            headers={'Content-Type': 'application/json'},
        )

        self._refresh_from_response(response=response)
        return self

    @handle_api_error
    def update(self) -> None:
        """Update an existing alert rule."""
        body: dict[str, Any] = {
            'critical_threshold': self.critical_threshold,
            'warning_threshold': self.warning_threshold,
            'evaluation_delay': self.evaluation_delay,
            'auto_threshold_params': self.auto_threshold_params,
        }

        response = self._client().patch(
            url=self._get_url(id_=self.id),
            json=body,
        )
        self._refresh_from_response(response=response)
        logger.info('Alert rule has been updated with properties: %s', json.dumps(body))

    @handle_api_error
    def enable_notifications(self) -> None:
        """Enable notifications for an alert rule"""
        self._client().patch(
            url=self._get_url(id_=self.id), json={'enable_notification': True}
        )
        logger.info(
            'notifications have been enabled for alert rule with id: %s', self.id
        )

    @handle_api_error
    def disable_notifications(self) -> None:
        """Disable notifications for an alert rule"""
        self._client().patch(
            url=self._get_url(id_=self.id), json={'enable_notification': False}
        )
        logger.info(
            'Notifications have been disabled for alert rule with id: %s', self.id
        )

    @handle_api_error
    def set_notification_config(
        self,
        emails: builtins.list[str] | None = None,
        pagerduty_services: builtins.list[str] | None = None,
        pagerduty_severity: str | None = None,
        webhooks: builtins.list[UUID] | None = None,
    ) -> NotificationConfig:
        """
        Set notification config for an alert rule

        :param emails: list of emails
        :param pagerduty_services: list of pagerduty services
        :param pagerduty_severity: severity of pagerduty
        :param webhooks: list of webhooks UUIDs

        :return: NotificationConfig object
        """

        # Validating input
        try:
            payload: dict[str, Any] = NotificationConfig(
                emails=emails,
                pagerduty_services=pagerduty_services,
                pagerduty_severity=pagerduty_severity,
                webhooks=webhooks,
            ).dict(exclude_none=True)
        except ValidationError as e:
            logger.exception('Invalid input: The format of input is not correct')
            raise e
        response = self._client().patch(
            url=self._get_notification_url(id_=self.id),
            data=payload,
            headers={'Content-Type': 'application/json'},
        )

        return NotificationConfig(**response.json()['data'])

    @handle_api_error
    def get_notification_config(self) -> NotificationConfig:
        """
        Get notifications config for an alert rule

        :return: NotificationConfig object
        """

        response = self._client().get(url=self._get_notification_url(id_=self.id))

        return NotificationConfig(**response.json()['data'])
