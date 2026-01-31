"""Alert rule constants and enumerations.

This module defines all constants used for configuring alert rules in the Fiddler platform,
including time bins, comparison types, conditions, priorities, and threshold algorithms.

Example:
    >>> from fiddler.constants.alert_rule import AlertCondition, Priority
    >>> condition = AlertCondition.GREATER
    >>> priority = Priority.HIGH
"""
import enum


@enum.unique
class BinSize(str, enum.Enum):
    """Time bin sizes for alert rule aggregation.

    Defines the time window granularity for aggregating metrics when evaluating alert rules.
    Smaller bin sizes provide more frequent monitoring but may be more sensitive to noise.

    Attributes:
        HOUR: Hourly aggregation - most granular monitoring
        DAY: Daily aggregation - balanced approach for most use cases
        WEEK: Weekly aggregation - good for trend monitoring
        MONTH: Monthly aggregation - suitable for long-term pattern detection

    Example:
        >>> alert_rule = AlertRule(
        ...     name="Hourly Drift Check",
        ...     bin_size=BinSize.HOUR,
        ...     # ... other parameters
        ... )
    """
    HOUR = 'Hour'
    DAY = 'Day'
    WEEK = 'Week'
    MONTH = 'Month'


@enum.unique
class CompareTo(str, enum.Enum):
    """Comparison baseline types for alert rule thresholds.

    Determines what the current metric value should be compared against when
    evaluating alert conditions.

    Attributes:
        TIME_PERIOD: Compare to a historical time period (relative comparison).
                    Useful for detecting changes over time, seasonal patterns, etc.
                    When using TIME_PERIOD, the compare_bin_delta parameter specifies
                    how many time periods back to compare against.
        RAW_VALUE: Compare to an absolute threshold value (absolute comparison).
                  Useful for hard limits and business rule enforcement.
                  When using RAW_VALUE, compare_bin_delta is ignored.

    Important:
        When using TIME_PERIOD, the allowed compare_bin_delta values depend on bin_size:

        +-------------+------------------------------------------+
        | Bin Size    | Allowed compare_bin_delta Values        |
        +=============+==========================================+
        | HOUR        | [1, 24, 168, 720, 2160]                 |
        |             | (1h, 1d, 1w, 1m, 3m ago)                |
        +-------------+------------------------------------------+
        | DAY         | [1, 7, 30, 90]                          |
        |             | (1d, 1w, 1m, 3m ago)                    |
        +-------------+------------------------------------------+
        | WEEK        | [1]                                      |
        |             | (1w ago only)                            |
        +-------------+------------------------------------------+
        | MONTH       | [1]                                      |
        |             | (1m ago only)                            |
        +-------------+------------------------------------------+

    Example:
        >>> # Compare current hourly drift to same hour yesterday (24 hours ago)
        >>> alert_rule = AlertRule(
        ...     compare_to=CompareTo.TIME_PERIOD,
        ...     bin_size=BinSize.HOUR,
        ...     compare_bin_delta=24  # 24 hours ago
        ... )
        >>>
        >>> # Compare daily metrics to last week (7 days ago)
        >>> alert_rule = AlertRule(
        ...     compare_to=CompareTo.TIME_PERIOD,
        ...     bin_size=BinSize.DAY,
        ...     compare_bin_delta=7  # 7 days ago
        ... )
        >>>
        >>> # Compare current accuracy to absolute minimum (no time comparison)
        >>> alert_rule = AlertRule(
        ...     compare_to=CompareTo.RAW_VALUE,
        ...     threshold=0.85  # Must be above 85%
        ... )
    """
    TIME_PERIOD = 'time_period'
    RAW_VALUE = 'raw_value'


@enum.unique
class AlertCondition(str, enum.Enum):
    """Alert trigger conditions for metric comparisons.

    Defines the comparison operator used to evaluate whether an alert should trigger
    based on the metric value and threshold.

    Attributes:
        GREATER: Trigger when metric value > threshold.
                Common for drift detection, error rates, latency spikes.
        LESSER: Trigger when metric value < threshold.
               Common for accuracy drops, traffic decreases, availability issues.

    Example:
        >>> # Alert when data drift exceeds 5%
        >>> drift_alert = AlertRule(
        ...     condition=AlertCondition.GREATER,
        ...     threshold=0.05
        ... )
        >>>
        >>> # Alert when model accuracy drops below 90%
        >>> accuracy_alert = AlertRule(
        ...     condition=AlertCondition.LESSER,
        ...     threshold=0.90
        ... )
    """
    GREATER = 'greater'
    LESSER = 'lesser'


@enum.unique
class Priority(str, enum.Enum):
    """Alert priority levels for notification routing and escalation.

    Determines the urgency and routing behavior of alert notifications.
    Higher priority alerts may trigger immediate notifications, phone calls,
    or escalation to on-call personnel.

    Attributes:
        HIGH: Critical issues requiring immediate attention.
              Examples: Model completely down, severe data quality issues.
        MEDIUM: Important issues that should be addressed promptly.
               Examples: Performance degradation, moderate drift.
        LOW: Minor issues for awareness and trend monitoring.
            Examples: Small drift increases, non-critical feature changes.

    Example:
        >>> # High priority for production model failures
        >>> critical_alert = AlertRule(
        ...     name="Model Down",
        ...     priority=Priority.HIGH
        ... )
        >>>
        >>> # Medium priority for performance monitoring
        >>> perf_alert = AlertRule(
        ...     name="Accuracy Drop",
        ...     priority=Priority.MEDIUM
        ... )
    """
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'


@enum.unique
class AlertThresholdAlgo(str, enum.Enum):
    """Threshold determination algorithms for alert rules.

    Defines how alert thresholds are calculated - either manually specified
    or automatically computed based on historical data patterns.

    Attributes:
        MANUAL: User-specified static thresholds.
               Provides full control but requires domain knowledge to set appropriately.
        STD_DEV_AUTO_THRESHOLD: Automatic thresholds based on standard deviation.
                               Calculates thresholds as mean ± (multiplier × std_dev)
                               from historical data. Adapts to data patterns automatically.

    Example:
        >>> # Manual threshold - user knows the acceptable drift limit
        >>> manual_alert = AlertRule(
        ...     threshold_type=AlertThresholdAlgo.MANUAL,
        ...     critical_threshold=0.1,
        ...     warning_threshold=0.05
        ... )
        >>>
        >>> # Auto threshold - let system learn from historical patterns
        >>> auto_alert = AlertRule(
        ...     threshold_type=AlertThresholdAlgo.STD_DEV_AUTO_THRESHOLD,
        ...     auto_threshold_params={
        ...         'warning_multiplier': 2.0,  # 2 std devs for warning
        ...         'critical_multiplier': 3.0  # 3 std devs for critical
        ...     }
        ... )
    """
    MANUAL = 'manual'
    STD_DEV_AUTO_THRESHOLD = 'standard_deviation_auto_threshold'

    def __str__(self) -> str:
        """Return the string value of the enum.

        Returns:
            str: The enum's string value for serialization and display.

        Example:
            >>> algo = AlertThresholdAlgo.MANUAL
            >>> str(algo)
            'manual'
        """
        return self.value
