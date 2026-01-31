# pylint: disable=E1101
# E1101: Instance of 'FieldInfo' has no 'type' member (no-member)
"""Baseline entity for drift detection and model performance monitoring.

The Baseline entity represents a reference dataset or time period that serves as the
foundation for detecting data drift, model performance degradation, and distributional
changes in production data. Baselines are essential for establishing expected behavior
patterns and triggering alerts when deviations occur.

Key Concepts:
    **Baseline Types**:
        - **Static Baseline**: Uses a fixed dataset as reference (training data)
        - **Rolling Window Baseline**: Uses a sliding time window as reference
        - **Previous Period Baseline**: Compares against a previous time period

    **Environment Types**:
        - **PRE_PRODUCTION**: Training/validation environment baselines
        - **PRODUCTION**: Production environment baselines for live monitoring

    **Time-based Configuration**:
        - **start_time/end_time**: Define the reference time period
        - **offset_delta**: Time offset for rolling comparisons
        - **window_bin_size**: Aggregation window for time-series analysis

    **Drift Detection**:
        Baselines enable detection of:
        - Feature drift (input data distribution changes)
        - Prediction drift (model output distribution changes)
        - Performance drift (accuracy, precision, recall changes)
        - Data quality drift (missing values, outliers, schema changes)

Typical Workflow:
    1. Create baseline from training data or stable production period
    2. Configure monitoring rules and alert thresholds
    3. Compare incoming production data against baseline
    4. Receive alerts when drift exceeds acceptable thresholds
    5. Update or recreate baselines as model evolves

Example:
    # Create training data baseline
    baseline = Baseline(
        name="training_baseline",
        model_id=model.id,
        environment=EnvType.PRE_PRODUCTION,
        dataset_id=training_dataset.id,
        type_="STATIC"
    ).create()

    # Create rolling window baseline
    rolling_baseline = Baseline(
        name="7day_rolling",
        model_id=model.id,
        environment=EnvType.PRODUCTION,
        type_="ROLLING_WINDOW",
        window_bin_size=WindowBinSize.DAY,
        offset_delta=7
    ).create()
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator
from uuid import UUID

from fiddler.constants.baseline import WindowBinSize
from fiddler.constants.dataset import EnvType
from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.entities.dataset import DatasetCompactMixin
from fiddler.entities.model import ModelCompactMixin
from fiddler.entities.project import ProjectCompactMixin
from fiddler.schemas.baseline import BaselineResp
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule
from fiddler.utils.helpers import raise_not_found


class Baseline(BaseEntity, ModelCompactMixin, ProjectCompactMixin, DatasetCompactMixin):  # pylint: disable=too-many-instance-attributes
    """Baseline for drift detection and model performance monitoring.

    A Baseline defines a reference point for comparing production data against expected
    patterns. It serves as the foundation for detecting data drift, model performance
    degradation, and distributional changes in ML systems.

    Attributes:
        name: Human-readable name for the baseline
        model_id: UUID of the associated :class:`~fiddler.entities.Model`
        type: Baseline type ("STATIC", "ROLLING_WINDOW", "PREVIOUS_PERIOD")
        environment: Environment type (:class:`~fiddler.constants.EnvType`)
        dataset_id: UUID of the reference :class:`~fiddler.entities.Dataset` (for static baselines)
        start_time: Start timestamp for time-based baselines (Unix timestamp)
        end_time: End timestamp for time-based baselines (Unix timestamp)
        offset_delta: Time offset in days for rolling/previous period baselines
        window_bin_size: Aggregation window (:class:`~fiddler.constants.WindowBinSize`)
        id: Unique identifier assigned after creation
        row_count: Number of records in the baseline dataset
        project_id: UUID of the containing :class:`~fiddler.entities.Project`
        created_at: Timestamp when baseline was created
        updated_at: Timestamp when baseline was last modified

    Example:
        # Create a static baseline from training data
        baseline = Baseline(
            name="production_baseline_v1",
            model_id=model.id,
            environment=EnvType.PRE_PRODUCTION,
            dataset_id=training_dataset.id,
            type_="STATIC"
        ).create()

        # Create a rolling 30-day baseline
        rolling_baseline = Baseline(
            name="rolling_30day",
            model_id=model.id,
            environment=EnvType.PRODUCTION,
            type_="ROLLING_WINDOW",
            window_bin_size=WindowBinSize.DAY,
            offset_delta=30
        ).create()

        # Monitor drift detection
        print(f"Baseline '{baseline.name}' has {baseline.row_count} records")
        print(f"Created: {baseline.created_at}")

    Note:
        Baselines are immutable once created. To modify baseline parameters,
        create a new baseline and update your monitoring configurations.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        model_id: UUID | str,
        environment: EnvType,
        type_: str,
        dataset_id: UUID | str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        offset_delta: int | None = None,
        window_bin_size: WindowBinSize | str | None = None,
    ) -> None:
        """Initialize a Baseline instance.

        Creates a baseline configuration for drift detection and monitoring. The baseline
        serves as a reference point for comparing production data against expected patterns.

        Args:
            name: Human-readable name for the baseline. Should be descriptive
                 and unique within the model context.
            model_id: UUID of the model this baseline belongs to. Must be a valid
                     model that exists in the Fiddler platform.
            environment: Environment type (PRE_PRODUCTION or PRODUCTION).
                        Determines the data environment this baseline monitors.
            type_: Baseline type. Supported values:
                  - "STATIC": Fixed dataset reference (requires dataset_id)
                  - "ROLLING_WINDOW": Sliding time window (requires offset_delta)
                  - "PREVIOUS_PERIOD": Previous time period comparison
            dataset_id: UUID of the reference dataset. Required for STATIC baselines,
                       optional for time-based baselines.
            start_time: Start timestamp for time-based baselines (Unix timestamp).
                       Defines the beginning of the reference period.
            end_time: End timestamp for time-based baselines (Unix timestamp).
                     Defines the end of the reference period.
            offset_delta: Time offset in days for rolling/previous period baselines.
                         For ROLLING_WINDOW: size of the sliding window.
                         For PREVIOUS_PERIOD: how far back to compare.
            window_bin_size: Aggregation window for time-series analysis.
                           Controls how data is grouped for comparison.

        Example:
            # Static baseline from training data
            baseline = Baseline(
                name="training_baseline_v2",
                model_id=model.id,
                environment=EnvType.PRE_PRODUCTION,
                dataset_id=training_dataset.id,
                type_="STATIC"
            )

            # Rolling 7-day window baseline
            rolling_baseline = Baseline(
                name="weekly_rolling",
                model_id=model.id,
                environment=EnvType.PRODUCTION,
                type_="ROLLING_WINDOW",
                offset_delta=7,
                window_bin_size=WindowBinSize.DAY
            )

            # Previous month comparison baseline
            monthly_baseline = Baseline(
                name="month_over_month",
                model_id=model.id,
                environment=EnvType.PRODUCTION,
                type_="PREVIOUS_PERIOD",
                offset_delta=30,
                window_bin_size=WindowBinSize.DAY
            )

        Note:
            After initialization, call create() to persist the baseline to the
            Fiddler platform. The baseline configuration cannot be modified
            after creation.
        """
        self.name = name
        self.model_id = model_id
        self.type = type_
        self.environment = environment
        self.dataset_id = dataset_id
        self.start_time = start_time
        self.end_time = end_time
        self.offset_delta = offset_delta
        self.window_bin_size = window_bin_size

        self.id: UUID | None = None
        self.row_count: int | None = None
        self.project_id: UUID | None = None
        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        # Deserialized response object
        self._resp: BaselineResp | None = None

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get model resource/item url."""
        url = '/v3/baselines'
        return url if not id_ else f'{url}/{id_}'

    @classmethod
    def _from_dict(cls, data: dict) -> Baseline:
        """Build entity object from the given dictionary."""

        # Deserialize the response
        resp_obj = BaselineResp(**data)

        # Initialize
        instance = cls(
            name=resp_obj.name,
            model_id=resp_obj.model.id,
            environment=resp_obj.dataset.type,
            dataset_id=resp_obj.dataset.id,
            type_=resp_obj.type,
            start_time=resp_obj.start_time,
            end_time=resp_obj.end_time,
            offset_delta=resp_obj.offset_delta,
            window_bin_size=resp_obj.window_bin_size,
        )

        # Add remaining fields
        fields = [
            'id',
            'created_at',
            'updated_at',
            'row_count',
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance.project_id = resp_obj.project.id
        instance._resp = resp_obj

        return instance

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = BaselineResp(**data)

        # Reset properties
        self.model_id = resp_obj.model.id
        self.environment = resp_obj.dataset.type
        self.dataset_id = resp_obj.dataset.id

        # Add remaining fields
        fields = [
            'id',
            'name',
            'type',
            'start_time',
            'end_time',
            'offset_delta',
            'window_bin_size',
            'created_at',
            'updated_at',
            'row_count',
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> Baseline:
        """Retrieve a baseline by its unique identifier.

        Fetches a baseline from the Fiddler platform using its UUID. This method
        returns the complete baseline configuration including metadata and statistics.

        Args:
            id_: The unique identifier (UUID) of the baseline to retrieve.
                Can be provided as a UUID object or string representation.

        Returns:
            :class:`~fiddler.entities.Baseline`: The baseline instance with all configuration
            and metadata populated from the server.

        Raises:
            NotFound: If no baseline exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Retrieve baseline by ID
            baseline = Baseline.get(id_="550e8400-e29b-41d4-a716-446655440000")
            print(f"Baseline: {baseline.name}")
            print(f"Type: {baseline.type}")
            print(f"Environment: {baseline.environment}")
            print(f"Records: {baseline.row_count}")

            # Check baseline configuration
            if baseline.type == "STATIC":
                print(f"Reference dataset: {baseline.dataset_id}")
            elif baseline.type == "ROLLING_WINDOW":
                print(f"Window size: {baseline.offset_delta} days")
                print(f"Bin size: {baseline.window_bin_size}")

        Note:
            This method makes an API call to fetch the latest baseline information
            from the server, including any updated statistics or metadata.
        """
        response = cls._client().get(url=cls._get_url(id_=id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def from_name(cls, name: str, model_id: UUID | str) -> Baseline:
        """
        Get the baseline instance of a model from baseline name

        :param name: Baseline name
        :param model_id: Model identifier

        :return: Baseline instance
        """

        _filter = QueryCondition(
            rules=[
                QueryRule(field='name', operator=OperatorType.EQUAL, value=name),
                QueryRule(
                    field='model_id',
                    operator=OperatorType.EQUAL,
                    value=model_id,
                ),
            ]
        )

        response = cls._client().get(
            url=cls._get_url(),
            params={'filter': _filter.json()},
        )
        if response.json()['data']['total'] == 0:
            raise_not_found('Baseline not found for the given identifier')

        return cls._from_dict(data=response.json()['data']['items'][0])

    @classmethod
    @handle_api_error
    def list(
        cls,
        model_id: UUID | str,
        type_: str | None = None,
        environment: EnvType | None = None,
    ) -> Iterator[Baseline]:
        """Get a list of all baselines of a model."""

        rules: list[QueryRule | QueryCondition] = []

        if type_:
            rules.append(
                QueryRule(field='type', operator=OperatorType.EQUAL, value=type_)
            )
        if environment:
            rules.append(
                QueryRule(
                    field='environment_type',
                    operator=OperatorType.EQUAL,
                    value=environment,
                )
            )

        _filter = QueryCondition(rules=rules)
        params: dict[str, Any] = {'filter': _filter.json()}

        url = f'/v3/models/{model_id}/baselines'
        for baseline in cls._paginate(url=url, params=params):
            yield cls._from_dict(data=baseline)

    @handle_api_error
    def create(self) -> Baseline:
        """Create a new baseline."""
        payload: dict[str, Any] = {
            'name': self.name,
            'model_id': self.model_id,
            'type': self.type,
            'env_type': self.environment,
            'env_id': self.dataset_id,
        }
        if self.start_time:
            payload['start_time'] = self.start_time
        if self.end_time:
            payload['end_time'] = self.end_time
        if self.offset_delta:
            payload['offset_delta'] = self.offset_delta
        if self.window_bin_size:
            payload['window_bin_size'] = self.window_bin_size

        response = self._client().post(
            url=self._get_url(),
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        self._refresh_from_response(response=response)
        return self

    @handle_api_error
    def delete(self) -> None:
        """Delete a baseline."""
        assert self.id is not None

        self._client().delete(url=self._get_url(id_=self.id))


@dataclass
class BaselineCompact:
    id: UUID
    name: str

    def fetch(self) -> Baseline:
        """Fetch baseline instance"""
        return Baseline.get(id_=self.id)


class BaselineCompactMixin:
    @property
    def baseline(self) -> BaselineCompact:
        """Baseline instance"""
        response = getattr(self, '_resp', None)
        if not response or not hasattr(response, 'baseline'):
            raise AttributeError(
                'This property is available only for objects generated from API '
                'response.'
            )

        return BaselineCompact(id=response.baseline.id, name=response.baseline.name)
