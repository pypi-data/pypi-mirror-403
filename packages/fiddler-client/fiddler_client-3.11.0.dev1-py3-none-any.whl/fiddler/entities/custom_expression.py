"""Custom Expression entities for advanced monitoring and data analysis.

This module contains entities for creating custom metrics and data segments that
extend Fiddler's built-in monitoring capabilities. Custom expressions enable
sophisticated analysis of model behavior, data quality, and business metrics
using SQL-like syntax for flexible data aggregation and filtering.

Key Concepts:
    **Custom Expressions**:
        Base class for user-defined analytical expressions that operate on
        model data. Expressions use SQL-like syntax to define calculations,
        aggregations, and filtering logic for advanced monitoring scenarios.

    **Custom Metrics**:
        User-defined metrics that calculate specific values from model data.
        Custom metrics enable monitoring of business-specific KPIs, domain-specific
        quality measures, and complex model performance indicators beyond standard
        ML metrics.

    **Segments**:
        Data segments that define subsets of model data based on specific criteria.
        Segments enable cohort analysis, A/B testing evaluation, and targeted
        monitoring of specific data populations or user groups.

    **Expression Syntax**:
        Expressions use SQL-like syntax with support for:
        - Aggregation functions (COUNT, AVG, SUM, MIN, MAX)
        - Conditional logic (CASE, WHERE, IF)
        - Mathematical operations (+, -, *, /, %)
        - Comparison operators (=, !=, <, >, <=, >=)
        - Logical operators (AND, OR, NOT)
        - String functions (LIKE, CONCAT, SUBSTRING)

    **Use Cases**:
        - **Business Metrics**: Revenue impact, conversion rates, customer satisfaction
        - **Data Quality**: Missing value rates, outlier detection, schema validation
        - **Fairness Monitoring**: Bias detection across demographic groups
        - **Performance Analysis**: Latency percentiles, error rates, throughput
        - **Cohort Analysis**: User behavior patterns, retention metrics

Typical Workflow:
    1. Define custom expression using SQL-like syntax
    2. Create CustomMetric or Segment with expression definition
    3. Validate expression syntax and test with sample data
    4. Use in AlertRules for automated monitoring
    5. Analyze results in dashboards and reports

Example:
    # Custom metric for conversion rate
    conversion_metric = CustomMetric(
        name="conversion_rate",
        model_id=model.id,
        definition="SUM(CASE WHEN prediction > 0.5 AND target = 1 THEN 1 ELSE 0 END) / COUNT(*)",
        description="Percentage of high-confidence predictions that convert"
    ).create()

    # Segment for high-value customers
    high_value_segment = Segment(
        name="high_value_customers",
        model_id=model.id,
        definition="customer_value > 10000 AND account_age > 365",
        description="Customers with high lifetime value and established accounts"
    ).create()

    # Custom metric for segment-specific accuracy
    segment_accuracy = CustomMetric(
        name="high_value_accuracy",
        model_id=model.id,
        definition="AVG(CASE WHEN prediction_class = target THEN 1.0 ELSE 0.0 END)",
        description="Accuracy for high-value customer segment"
    ).create()
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Iterator
from uuid import UUID

from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.entities.model import ModelCompactMixin
from fiddler.entities.project import ProjectCompactMixin
from fiddler.schemas.custom_expression import (
    CustomExpressionResp,
    CustomMetricResp,
    SegmentResp,
)
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule
from fiddler.utils.helpers import raise_not_found


class CustomExpression(BaseEntity, ModelCompactMixin, ProjectCompactMixin):
    """Base class for custom expressions in Fiddler monitoring.

    CustomExpression provides the foundation for creating user-defined analytical
    expressions that operate on model data. This abstract base class defines the
    common interface and functionality shared by CustomMetric and Segment entities.

    Attributes:
        name: Human-readable name for the custom expression. Should be descriptive
             and follow naming conventions for the specific expression type.
        model_id: UUID of the associated :class:`~fiddler.entities.Model`
        definition: SQL-like expression definition that specifies the calculation
                   or filtering logic to be applied to model data.
        description: Optional human-readable description explaining the purpose
                    and usage of the custom expression.
        id: Unique identifier assigned after creation
        created_at: Timestamp when the custom expression was created

    Note:
        This is an abstract base class. Use CustomMetric or Segment subclasses
        for creating specific types of custom expressions.
    """

    def __init__(
        self,
        name: str,
        model_id: UUID | str,
        definition: str,
        description: str | None = None,
    ) -> None:
        """Construct a CustomExpression instance.

        Args:
            name: Human-readable name for the CustomExpression.
                 Should be descriptive and follow naming conventions.
            model_id: UUID or string identifier of the associated Model.
            definition: Fiddler Query Language (FQL) expression defining the calculation
                       or filtering logic. Uses SQL-like syntax with functions like
                       sum(), average(), if(), is_null(), etc.
            description: Optional human-readable description explaining the purpose
                        and usage of the CustomExpression.
        """
        self.name = name
        self.model_id = model_id
        self.definition = definition
        self.description = description

        self.id: UUID | None = None
        self.created_at: datetime | None = None

        # Deserialized response object
        self._resp: CustomExpressionResp | None = None

    @classmethod
    def _get_url(cls, id_: UUID | str | None = None) -> str:
        """Get custom expression resource/item url."""
        url = f"/v3/{cls._get_url_path()}"
        return url if not id_ else f"{url}/{id_}"

    @staticmethod
    @abstractmethod
    def _get_url_path() -> str:
        """Get custom expression resource path"""

    @staticmethod
    @abstractmethod
    def _get_display_name() -> str:
        """Get custom expression display name"""

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = CustomMetricResp(**data)
        assert self.model_id
        fields = [
            "id",
            "name",
            "definition",
            "description",
            "created_at",
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @classmethod
    def _from_dict(cls, data: dict) -> CustomExpression:
        """Build entity object from the given dictionary."""

        # Deserialize the response
        resp_obj = CustomMetricResp(**data)

        # Initialize
        instance = cls(
            name=resp_obj.name,
            model_id=resp_obj.model.id,
            definition=resp_obj.definition,
            description=resp_obj.description,
        )

        # Add remaining fields
        fields = [
            "id",
            "created_at",
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj

        return instance

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> CustomExpression:
        """Retrieve a CustomExpression by its unique identifier.

        Fetches a CustomExpression from the Fiddler platform using its UUID.

        Args:
            id_: The unique identifier (UUID) of the CustomExpression to retrieve.
                Can be provided as a UUID object or string representation.

        Returns:
            The CustomExpression instance with all its configuration and metadata.

        Raises:
            NotFound: If no CustomExpression exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.
        """
        response = cls._client().get(url=cls._get_url(id_=id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def from_name(cls, name: str, model_id: UUID | str) -> CustomExpression:
        """Retrieve a CustomExpression by name and model.

        Fetches a CustomExpression from the Fiddler platform using its name
        and associated model ID.

        Args:
            name: The name of the CustomExpression to retrieve.
            model_id: UUID or string identifier of the associated Model.

        Returns:
            The CustomExpression instance for the provided parameters.

        Raises:
            NotFound: If no CustomExpression exists with the specified name and model.
            ApiError: If there's an error communicating with the Fiddler API.
        """

        _filter = QueryCondition(
            rules=[
                QueryRule(field="name", operator=OperatorType.EQUAL, value=name),
                QueryRule(
                    field="model_id", operator=OperatorType.EQUAL, value=model_id
                ),
            ]
        )
        params: dict[str, Any] = {
            "filter": _filter.json(),
        }

        response = cls._client().get(
            url=cls._get_url(),
            params=params,
        )
        if response.json()["data"]["total"] == 0:
            raise_not_found(
                f"{cls._get_display_name()} not found for the given identifier"
            )

        return cls._from_dict(data=response.json()["data"]["items"][0])

    @classmethod
    @handle_api_error
    def list(
        cls,
        model_id: UUID | str,
    ) -> Iterator[CustomExpression]:
        """List all CustomExpression instances for a model.

        Retrieves all CustomExpression instances associated with a specific model.

        Args:
            model_id: UUID or string identifier of the Model.

        Yields:
            CustomExpression instances for each CustomExpression in the model.

        Raises:
            ApiError: If there's an error communicating with the Fiddler API.
        """

        url = f"/v3/models/{model_id}/{cls._get_url_path()}"

        for item in cls._paginate(url=url):
            yield cls._from_dict(data=item)

    @handle_api_error
    def create(self) -> CustomExpression:
        """Create a new CustomExpression on the Fiddler platform.

        Registers this CustomExpression with the Fiddler platform. The expression
        must have a name, model_id, and definition specified before calling create().

        Returns:
            The same CustomExpression instance with updated server-side attributes
            (id, created_at, etc.).

        Raises:
            ApiError: If there's an error communicating with the Fiddler API.
            Conflict: If a CustomExpression with the same name already exists for this model.
        """
        payload = {
            "model_id": self.model_id,
            "name": self.name,
            "definition": self.definition,
        }

        if self.description:
            payload["description"] = self.description

        response = self._client().post(
            url=self._get_url(),
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        self._refresh_from_response(response=response)
        return self

    @handle_api_error
    def delete(self) -> None:
        """Delete this CustomExpression from the Fiddler platform.

        Permanently removes the CustomExpression. This action cannot be undone.
        Any alert rules or monitors using this CustomExpression must be deleted first.

        Raises:
            NotFound: If the CustomExpression no longer exists.
            ApiError: If there's an error communicating with the Fiddler API.
            Conflict: If the CustomExpression is still being used by alert rules or monitors.
        """
        assert self.id is not None

        self._client().delete(url=self._get_url(id_=self.id))


class CustomMetric(CustomExpression):
    """Custom metric for monitoring business-specific and domain-specific KPIs.

    CustomMetric enables creation of user-defined metrics that calculate specific
    values from model data using SQL-like expressions. Custom metrics extend
    Fiddler's built-in monitoring capabilities to support business requirements,
    domain-specific quality measures, and complex performance indicators.

    Attributes:
        Inherits all attributes from :class:`~fiddler.entities.CustomExpression`.

    Example:
        # Business conversion rate metric
        conversion_rate = CustomMetric(
            name="weekly_conversion_rate",
            model_id=model.id,
            definition="sum(if(prediction_score > 0.7 and converted == 1, 1, 0)) / sum(if(prediction_score > 0.7, 1, 0))",
            description="Conversion rate for high-confidence predictions"
        ).create()

        # Data quality metric
        missing_rate = CustomMetric(
            name="feature_missing_rate",
            model_id=model.id,
            definition="sum(if(is_null(income), 1, 0)) / count(income)",
            description="Percentage of records with missing income values"
        ).create()

        # Fairness metric
        fairness_metric = CustomMetric(
            name="demographic_parity",
            model_id=model.id,
            definition="abs((sum(if(gender == 'Male', predicted_churn, 0)) / sum(if(gender == 'Male', 1, 0))) - (sum(if(gender == 'Female', predicted_churn, 0)) / sum(if(gender == 'Female', 1, 0))))",
            description="Demographic parity difference between gender groups"
        ).create()

        # Use in alert rule
        alert_rule = AlertRule(
            name="conversion_rate_alert",
            model_id=model.id,
            metric_id=conversion_rate.id,
            priority=Priority.HIGH,
            compare_to=CompareTo.TIME_PERIOD,
            condition=AlertCondition.LESSER,
            bin_size=BinSize.DAY,
            critical_threshold=0.15,  # Alert if conversion drops below 15%
            compare_bin_delta=7
        ).create()

    Note:
        Custom metrics are calculated during data ingestion and monitoring cycles.
        Complex expressions may impact performance, so optimize for efficiency.
        Test expressions thoroughly before using in production alert rules.
    """

    def __init__(
        self,
        name: str,
        model_id: UUID | str,
        definition: str,
        description: str | None = None,
    ) -> None:
        """Construct a custom metric instance."""
        super().__init__(name, model_id, definition, description)

        # Deserialized response object
        self._resp: CustomMetricResp | None = None

    @staticmethod
    def _get_url_path() -> str:
        return "custom-metrics"

    @staticmethod
    def _get_display_name() -> str:
        return "Custom metric"


class Segment(CustomExpression):
    """Data segment for targeted monitoring and cohort analysis.

    Segment defines subsets of model data based on specific criteria using SQL-like
    expressions. Segments enable cohort analysis, A/B testing evaluation, targeted
    monitoring of specific populations, and fairness analysis across different groups.

    Attributes:
        Inherits all attributes from :class:`~fiddler.entities.CustomExpression`.

    Example:
        # High-value customer segment
        high_value_segment = Segment(
            name="high_value_customers",
            model_id=model.id,
            definition="customer_lifetime_value > 10000 and account_age_days > 365",
            description="Customers with high LTV and established accounts"
        ).create()

        # Geographic segment
        west_coast_segment = Segment(
            name="west_coast_users",
            model_id=model.id,
            definition="state == 'CA' or state == 'OR' or state == 'WA'",
            description="Users from West Coast states"
        ).create()

        # Risk-based segment
        high_risk_segment = Segment(
            name="high_risk_applications",
            model_id=model.id,
            definition="credit_score < 600 or debt_to_income > 0.4",
            description="Loan applications with elevated risk factors"
        ).create()

        # Age-based demographic segment
        young_adults_segment = Segment(
            name="young_adults",
            model_id=model.id,
            definition="age >= 18 and age <= 35",
            description="Young adult demographic (18-35 years)"
        ).create()

        # Use segment in alert rule for targeted monitoring
        segment_alert = AlertRule(
            name="high_value_drift_alert",
            model_id=model.id,
            metric_id="drift_score",
            priority=Priority.HIGH,
            compare_to=CompareTo.BASELINE,
            condition=AlertCondition.GT,
            bin_size=BinSize.HOUR,
            critical_threshold=0.7,
            baseline_id=baseline.id,
            segment_id=high_value_segment.id
        ).create()

    Note:
        Segments are evaluated during data processing and can be used with any
        monitoring metric. Complex segment definitions may impact performance,
        so optimize for efficiency. Segments are particularly useful for fairness
        monitoring and business-critical cohort analysis.
    """

    def __init__(
        self,
        name: str,
        model_id: UUID | str,
        definition: str,
        description: str | None = None,
    ) -> None:
        """Construct a segment instance."""
        super().__init__(name, model_id, definition, description)

        # Deserialized response object
        self._resp: SegmentResp | None = None

    @staticmethod
    def _get_url_path() -> str:
        return "segments"

    @staticmethod
    def _get_display_name() -> str:
        return "Segment"
