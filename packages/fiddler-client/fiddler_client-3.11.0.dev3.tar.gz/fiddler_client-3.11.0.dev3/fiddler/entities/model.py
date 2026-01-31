# pylint: disable=too-many-lines
"""Model entity for managing ML models in the Fiddler platform.

This module provides the Model class for creating, managing, and monitoring machine learning
models within Fiddler. Models represent ML systems that can be monitored for drift,
performance, and explainability.

Key Features:
    - Create models from DataFrames, files, or manual schema/spec definition
    - Publish production and pre-production data for monitoring
    - Upload and manage model artifacts for serving
    - Generate surrogate models for explainability
    - Monitor model performance and data drift
    - Integrate with alert systems and baselines

Example:
    import fiddler
    import pandas as pd

    # Initialize connection
    fiddler.init(url="https://your-instance.com", token="your-token")

    # Create model from DataFrame
    df = pd.read_csv("training_data.csv")
    model = fiddler.Model.from_data(
        source=df,
        name="fraud_detection_v1",
        project_id=project.id,
        task=fiddler.ModelTask.BINARY_CLASSIFICATION,
        description="Credit card fraud detection model"
    )
    model.create()

    # Publish production data
    prod_data = pd.read_csv("production_events.csv")
    job = model.publish(source=prod_data, environment=fiddler.EnvType.PRODUCTION)
"""

from __future__ import annotations

import builtins
import logging
import typing
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID

import pandas as pd

from fiddler.constants.dataset import EnvType
from fiddler.constants.model import ModelInputType, ModelTask
from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.entities.events import EventPublisher
from fiddler.entities.job import Job
from fiddler.entities.model_artifact import ModelArtifact
from fiddler.entities.model_deployment import ModelDeployment
from fiddler.entities.project import ProjectCompactMixin
from fiddler.entities.surrogate import Surrogate
from fiddler.entities.user import CreatedByMixin, UpdatedByMixin
from fiddler.entities.xai import XaiMixin
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule
from fiddler.schemas.job import JobCompactResp
from fiddler.schemas.model import ModelResp
from fiddler.schemas.model_deployment import DeploymentParams
from fiddler.schemas.model_schema import Column, ModelSchema
from fiddler.schemas.model_spec import ModelSpec
from fiddler.schemas.model_task_params import ModelTaskParams
from fiddler.schemas.xai_params import XaiParams
from fiddler.utils.helpers import raise_not_found
from fiddler.utils.model_generator import ModelGenerator

if typing.TYPE_CHECKING:
    from fiddler.entities.baseline import Baseline
    from fiddler.entities.dataset import Dataset

logger = logging.getLogger(__name__)


class Model(
    BaseEntity,
    CreatedByMixin,
    ProjectCompactMixin,
    UpdatedByMixin,
    XaiMixin,
):  # pylint: disable=too-many-ancestors
    """Represents a machine learning model in the Fiddler platform.

    The Model class is the central entity for ML model monitoring and management.
    It encapsulates the model's schema, specification, and metadata, and provides
    methods for data publishing, artifact management, and monitoring operations.

    Key Concepts:
        - **Schema** (:class:`~fiddler.schemas.ModelSchema`): Defines the structure and data types of model inputs/outputs
        - **Spec** (:class:`~fiddler.schemas.ModelSpec`): Defines how columns are used (features, targets, predictions, etc.)
        - **Task** (:class:`~fiddler.constants.ModelTask`): The ML task type (classification, regression, ranking, etc.)
        - **Artifacts** (:class:`~fiddler.entities.ModelArtifact`): Deployable model code and dependencies
        - **Surrogates** (:class:`~fiddler.entities.Surrogate`): Simplified models for fast explanations

    Lifecycle:
        1. Create model with schema/spec (from data or manual definition)
        2. Upload model artifacts for serving (optional)
        3. Publish baseline/training data for drift detection
        4. Publish production data for monitoring
        5. Set up alerts and monitoring rules

    Common Use Cases:
        - **Tabular Models**: Traditional ML models with structured data
        - **Text Models**: NLP models with text inputs and embeddings
        - **Mixed Models**: Models combining tabular and unstructured data
        - **Ranking Models**: Recommendation and search ranking systems
        - **LLM Models**: Large language model monitoring

    Attributes:
        name (str): Model name, unique within a project version
        version (str, optional): Model version identifier
        project_id (UUID | str): Parent project identifier
        schema (:class:`~fiddler.schemas.ModelSchema`): Column definitions and data types
        spec (:class:`~fiddler.schemas.ModelSpec`): Column usage specification (inputs, outputs, targets)
        input_type (:class:`~fiddler.constants.ModelInputType`): Type of input data (TABULAR, TEXT, MIXED)
        task (:class:`~fiddler.constants.ModelTask`): ML task type (BINARY_CLASSIFICATION, REGRESSION, etc.)
        task_params (:class:`~fiddler.schemas.ModelTaskParams`): Task-specific parameters
        description (str, optional): Human-readable model description
        event_id_col (str, optional): Column name for unique event identifiers
        event_ts_col (str, optional): Column name for event timestamps
        event_ts_format (str, optional): Timestamp format string
        xai_params (:class:`~fiddler.schemas.XaiParams`): Explainability configuration

    Example:
        # Create model from DataFrame with automatic schema detection
        import pandas as pd
        df = pd.DataFrame({
            'age': [25, 35, 45],
            'income': [50000, 75000, 100000],
            'approved': [0, 1, 1]  # target
        })

        model = Model.from_data(
            source=df,
            name="credit_approval",
            project_id=project.id,
            task=ModelTask.BINARY_CLASSIFICATION,
            description="Credit approval model v1.0"
        )
        model.create()

        # Publish production events
        events = [
            {'age': 30, 'income': 60000, 'prediction': 0.8},
            {'age': 40, 'income': 80000, 'prediction': 0.9}
        ]
        event_ids = model.publish(source=events)

        # Get model info
        print(f"Model: {model.name} (Task: {model.task})")
        print(f"Columns: {len(model.schema.columns)}")
        print(f"Features: {model.spec.inputs}")
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        project_id: UUID | str,
        schema: ModelSchema,
        spec: ModelSpec,
        version: str | None = None,
        input_type: str = ModelInputType.TABULAR,
        task: str = ModelTask.NOT_SET,
        task_params: ModelTaskParams | None = None,
        description: str | None = None,
        event_id_col: str | None = None,
        event_ts_col: str | None = None,
        event_ts_format: str | None = None,
        xai_params: XaiParams | None = None,
    ) -> None:
        """Initialize a Model instance.

        Creates a new Model object with the specified configuration. The model is not
        created on the Fiddler platform until .create() is called.

        Args:
            name: Model name, must be unique within the project version.
                 Should be descriptive and follow naming conventions.
            project_id: UUID or string identifier of the parent project.
            schema: :class:`~fiddler.schemas.ModelSchema` defining column structure and data types.
                   Can be created manually or generated from data.
            spec: :class:`~fiddler.schemas.ModelSpec` defining how columns are used (inputs, outputs, targets).
                 Specifies the model's interface and column roles.
            version: Optional version identifier. If not provided, defaults to 'v1'.
                    Used for model versioning and A/B testing.
            input_type: :class:`~fiddler.constants.ModelInputType` - Type of input data the model processes.
                       - TABULAR: Structured/tabular data (default)
                       - TEXT: Natural language text data
                       - MIXED: Combination of structured and unstructured data
            task: :class:`~fiddler.constants.ModelTask` - Machine learning task type.
                 - BINARY_CLASSIFICATION: Binary classification (0/1, True/False)
                 - MULTICLASS_CLASSIFICATION: Multi-class classification
                 - REGRESSION: Continuous value prediction
                 - RANKING: Ranking/recommendation tasks
                 - LLM: Large language model tasks
                 - NOT_SET: Task not specified (default)
            task_params: :class:`~fiddler.schemas.ModelTaskParams` - Task-specific parameters like classification thresholds,
                        class weights, or ranking parameters.
            description: Human-readable description of the model's purpose,
                        training data, or other relevant information.
            event_id_col: Column name containing unique identifiers for each
                         prediction event. Used for event tracking and updates.
            event_ts_col: Column name containing event timestamps.
                         Used for time-based analysis and drift detection.
            event_ts_format: Format string for parsing timestamps in event_ts_col.
                           Examples: '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'
            xai_params: :class:`~fiddler.schemas.XaiParams` - Configuration for explainability features like
                       explanation methods and custom feature definitions.

        Example:
            from fiddler.schemas import ModelSchema, ModelSpec, Column
            from fiddler.constants import DataType, ModelTask

            # Manual schema/spec creation
            schema = ModelSchema(columns=[
                Column(name='age', data_type=DataType.INTEGER),
                Column(name='income', data_type=DataType.FLOAT),
                Column(name='prediction', data_type=DataType.FLOAT)
            ])

            spec = ModelSpec(
                inputs=['age', 'income'],
                outputs=['prediction']
            )

            model = Model(
                name="manual_model",
                project_id="project-uuid",
                schema=schema,
                spec=spec,
                task=ModelTask.REGRESSION,
                description="Manually defined regression model"
            )

        Note:
            The model exists only locally until .create() is called. Use Model.from_data()
            for automatic schema/spec generation from DataFrames or files.
        """
        self.name = name
        self.version = version
        self.project_id = project_id
        self.schema = schema
        self.input_type = input_type
        self.task = task
        self.description = description
        self.event_id_col = event_id_col
        self.event_ts_col = event_ts_col
        self.event_ts_format = event_ts_format
        self.spec = spec
        self.task_params = task_params or ModelTaskParams()
        self.xai_params = xai_params or XaiParams()

        self.id: UUID | None = None
        self.artifact_status: str | None = None
        self.artifact_files: list[dict] | None = None
        self.is_binary_ranking_model: bool | None = None
        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

        # Deserialized response object
        self._resp: ModelResp | None = None

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get model resource/item url."""
        url = '/v3/models'
        return url if not id_ else f'{url}/{id_}'

    @classmethod
    def _from_dict(cls, data: dict) -> Model:
        """Build entity object from the given dictionary."""

        # Deserialize the response
        resp_obj = ModelResp(**data)

        # Initialize
        instance = cls(
            name=resp_obj.name,
            version=resp_obj.version,
            schema=resp_obj.schema_,
            spec=resp_obj.spec,
            project_id=resp_obj.project.id,
            input_type=resp_obj.input_type,
            task=resp_obj.task,
            task_params=resp_obj.task_params,
            description=resp_obj.description,
            event_id_col=resp_obj.event_id_col,
            event_ts_col=resp_obj.event_ts_col,
            event_ts_format=resp_obj.event_ts_format,
            xai_params=resp_obj.xai_params,
        )

        # Add remaining fields
        fields = [
            'id',
            'created_at',
            'updated_at',
            'artifact_status',
            'artifact_files',
            'is_binary_ranking_model',
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj
        return instance

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = ModelResp(**data)

        # Reset fields
        self.schema = resp_obj.schema_
        self.project_id = resp_obj.project.id

        fields = [
            'id',
            'name',
            'version',
            'spec',
            'input_type',
            'task',
            'task_params',
            'description',
            'event_id_col',
            'event_ts_col',
            'event_ts_format',
            'xai_params',
            'created_at',
            'updated_at',
            'artifact_status',
            'artifact_files',
            'is_binary_ranking_model',
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @cached_property
    def _artifact(self) -> ModelArtifact:
        """Model artifact instance"""
        assert self.id is not None
        return ModelArtifact(model_id=self.id)

    @cached_property
    def _surrogate(self) -> Surrogate:
        """Model artifact instance"""
        assert self.id is not None
        return Surrogate(model_id=self.id)

    @cached_property
    def _event_publisher(self) -> EventPublisher:
        """Event publisher instance"""
        assert self.id is not None
        return EventPublisher(model_id=self.id)

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> Model:
        """Retrieve a model by its unique identifier.

        Fetches a model from the Fiddler platform using its UUID. This is the most
        direct way to retrieve a model when you know its ID.

        Args:
            id_: The unique identifier (UUID) of the model to retrieve.
                Can be provided as a UUID object or string representation.

        Returns:
            Model: The model instance with all its configuration and metadata.

        Raises:
            NotFound: If no model exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get model by UUID
            model = Model.get(id_="550e8400-e29b-41d4-a716-446655440000")
            print(f"Retrieved model: {model.name} (Task: {model.task})")

            # Access model properties
            print(f"Project ID: {model.project_id}")
            print(f"Input columns: {model.spec.inputs}")
            print(f"Created: {model.created_at}")

        Note:
            This method makes an API call to fetch the latest model state from the server.
            The returned model instance reflects the current state in Fiddler.
        """
        response = cls._client().get(url=cls._get_url(id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def from_name(
        cls,
        name: str,
        project_id: UUID | str,
        version: str | None = None,
        latest: bool = False,
    ) -> Model:
        """Retrieve a model by name within a project.

        Finds and returns a model using its name and project context. This is useful
        when you know the model name but not its UUID. Supports version-specific
        retrieval and latest version lookup.

        Args:
            name: The name of the model to retrieve. Model names are unique
                 within a project but may have multiple versions.
            project_id: UUID or string identifier of the project containing the model.
            version: Specific version name to retrieve. If None, behavior depends
                    on the 'latest' parameter.
            latest: If True and version is None, retrieves the most recently created
                   version. If False, retrieves the first (oldest) version.
                   Ignored if version is specified.

        Returns:
            Model: The model instance matching the specified criteria.

        Raises:
            NotFound: If no model exists with the specified name/version in the project.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get specific version
            model = Model.from_name(
                name="fraud_detector",
                project_id=project.id,
                version="v2.1"
            )

            # Get latest version
            latest_model = Model.from_name(
                name="fraud_detector",
                project_id=project.id,
                latest=True
            )

            # Get first version (default behavior)
            first_model = Model.from_name(
                name="fraud_detector",
                project_id=project.id
            )

            print(f"Model versions: {first_model.version} -> {latest_model.version}")

        Note:
            When version is None and latest=False, returns the first version created.
            This provides consistent behavior for accessing the "original" model version.
        """
        _filter = QueryCondition(
            rules=[
                QueryRule(field='name', operator=OperatorType.EQUAL, value=name),
                QueryRule(
                    field='project_id',
                    operator=OperatorType.EQUAL,
                    value=project_id,
                ),
            ]
        )

        if version:
            _filter.add_rule(
                QueryRule(field='version', operator=OperatorType.EQUAL, value=version)
            )

        ordering = '-created_at' if latest else 'created_at'
        response = cls._client().get(
            url=cls._get_url(),
            params={'filter': _filter.json(), 'limit': 1, 'ordering': ordering},
        )

        if response.json()['data']['total'] == 0:
            raise_not_found('Model not found for the given identifier')

        return cls.get(id_=response.json()['data']['items'][0]['id'])

    @handle_api_error
    def create(self) -> Model:
        """Create the model on the Fiddler platform.

        Persists this model instance to the Fiddler platform, making it available
        for monitoring, data publishing, and other operations. The model must have
        a valid schema, spec, and be associated with an existing project.

        Returns:
            Model: This model instance, updated with server-assigned fields like
                  ID, creation timestamp, and other metadata.

        Raises:
            Conflict: If a model with the same name and version already exists
                     in the project.
            ValidationError: If the model configuration is invalid (e.g., invalid
                           schema, spec, or task parameters).
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Create model from DataFrame
            model = Model.from_data(
                source=training_df,
                name="churn_predictor",
                project_id=project.id,
                task=ModelTask.BINARY_CLASSIFICATION
            )

            # Create on platform
            created_model = model.create()
            print(f"Created model with ID: {created_model.id}")
            print(f"Created at: {created_model.created_at}")

            # Model is now available for monitoring
            assert created_model.id is not None

            # Can now publish data, set up alerts, etc.
            job = created_model.publish(source=production_data)

        Note:
            After successful creation, the model instance is updated in-place with
            server-assigned metadata. The same instance can be used for subsequent
            operations without needing to fetch it again.
        """
        payload = {
            'name': self.name,
            'project_id': str(self.project_id),
            'schema': self.schema.dict(),
            'spec': self.spec.dict(),
            'input_type': self.input_type,
            'task': self.task,
            'task_params': self.task_params.dict(),
            'description': self.description,
            'event_id_col': self.event_id_col,
            'event_ts_col': self.event_ts_col,
            'event_ts_format': self.event_ts_format,
            'xai_params': self.xai_params.dict(),
        }

        if self.version:
            payload['version'] = self.version

        response = self._client().post(
            url=self._get_url(),
            # The above seems to be safe for stdlib JSON-encoding.
            json=payload,
        )
        self._refresh_from_response(response=response)
        return self

    @handle_api_error
    def update(self) -> None:
        """Update an existing model."""
        body: dict[str, Any] = {
            'version': self.version,
            'xai_params': self.xai_params.dict(),
            'description': self.description,
            'event_id_col': self.event_id_col,
            'event_ts_col': self.event_ts_col,
            'event_ts_format': self.event_ts_format,
        }

        response = self._client().patch(
            url=self._get_url(id_=self.id),
            # object seems safe for stdlib JSON-encoding
            json=body,
        )
        self._refresh_from_response(response=response)

    @handle_api_error
    def add_column(
        self,
        column: Column,
        column_type: str = 'metadata',
    ) -> None:
        """Add a new column to the model schema.

        Updates both the schema and spec to include the new column. This allows
        you to extend your model with additional columns after initial creation.

        .. versionadded:: 3.11.0

        Args:
            column: Column object defining the new column's properties (name, data_type, etc.)
            column_type: Type of column in spec. One of: 'inputs', 'outputs', 'targets',
                        'decisions', 'metadata'. Defaults to 'metadata'.

        Raises:
            ValueError: If column already exists or column_type is invalid
            BadRequest: If column definition is invalid per backend validation

        Example:
            # Add a numeric metadata column
            new_col = Column(
                name="customer_segment",
                data_type=DataType.INTEGER,
                min=1,
                max=5
            )
            model.add_column(column=new_col, column_type='metadata')

            # Add a categorical feature
            category_col = Column(
                name="region",
                data_type=DataType.CATEGORY,
                categories=["US", "EU", "APAC"]
            )
            model.add_column(column=category_col, column_type='inputs')

        Note:
            - Adding a column doesn't populate historical data; new column will be null
              for past events
            - Column names must be unique within the model
            - After adding a column, include it in future event publishing
        """
        valid_column_types = [
            'inputs',
            'outputs',
            'targets',
            'decisions',
            'metadata',
        ]

        if column_type not in valid_column_types:
            raise ValueError(
                f"column_type must be one of {valid_column_types}, got: '{column_type}'"
            )

        # Check if column already exists
        existing_names = [col.name for col in self.schema.columns]
        if column.name in existing_names:
            raise ValueError(
                f"Column '{column.name}' already exists in model schema. "
                f'Cannot add existing column.'
            )

        # Create updated schema with new column
        updated_columns = [col.dict() for col in self.schema.columns] + [column.dict()]

        # Create updated spec with new column
        updated_spec = self.spec.dict()
        current_list = updated_spec.get(column_type) or []
        updated_spec[column_type] = current_list + [column.name]

        body: dict[str, Any] = {
            'schema': {'columns': updated_columns},
            'spec': updated_spec,
        }

        response = self._client().patch(
            url=self._get_url(id_=self.id),
            json=body,
        )

        self._refresh_from_response(response=response)

    @classmethod
    @handle_api_error
    def list(
        cls, project_id: UUID | str, name: str | None = None
    ) -> Iterator[ModelCompact]:
        """List models in a project with optional filtering.

        Retrieves all models or model versions within a project. Returns lightweight
        ModelCompact objects that can be used to fetch full Model instances when needed.

        Args:
            project_id: UUID or string identifier of the project to search within.
            name: Optional model name filter. If provided, returns all versions
                 of the specified model. If None, returns all models in the project.

        Yields:
            ModelCompact: Lightweight model objects containing id, name, and version.
                         Call .fetch() on any ModelCompact to get the full Model instance.

        Example:
            # List all models in project
            for model_compact in Model.list(project_id=project.id):
                print(f"Model: {model_compact.name} v{model_compact.version}")
                print(f"  ID: {model_compact.id}")

            # List all versions of a specific model
            for version in Model.list(project_id=project.id, name="fraud_detector"):
                print(f"Version: {version.version}")
            ...
                # Get full model details if needed
                full_model = version.fetch()
                print(f"  Task: {full_model.task}")
                print(f"  Created: {full_model.created_at}")

            # Convert to list for counting
            models = list(Model.list(project_id=project.id))
            print(f"Total models in project: {len(models)}")

        Note:
            This method returns an iterator for memory efficiency when dealing with
            many models. The ModelCompact objects are lightweight and don't include
            full schema/spec information - use .fetch() when you need complete details.
        """
        _filter = QueryCondition(
            rules=[
                QueryRule(
                    field='project_id', operator=OperatorType.EQUAL, value=project_id
                ),
            ]
        )

        if name:
            _filter.add_rule(
                QueryRule(field='name', operator=OperatorType.EQUAL, value=name)
            )

        params = {'filter': _filter.json()}

        for model in cls._paginate(url=cls._get_url(), params=params):
            yield ModelCompact(
                id=model['id'], name=model['name'], version=model['version']
            )

    def duplicate(self, version: str | None = None) -> Model:
        """
        Duplicate the model instance with the given version name.

        This call will not save the model on server. After making changes to the model
        instance call .create() to add the model version to Fiddler Platform.

        :param version: Version name for the new instance
        :return: Model instance
        """
        return Model(
            name=self.name,
            project_id=self.project_id,
            schema=deepcopy(self.schema),
            spec=deepcopy(self.spec),
            version=version if version else self.version,
            input_type=self.input_type,
            task=self.task,
            task_params=deepcopy(self.task_params),
            description=self.description,
            event_id_col=self.event_id_col,
            event_ts_col=self.event_ts_col,
            event_ts_format=self.event_ts_format,
            xai_params=deepcopy(self.xai_params),
        )

    @property
    def datasets(self) -> Iterator[Dataset]:
        """Get all datasets associated with this model.

        Returns an iterator over all datasets that have been published to this model,
        including both production data and pre-production datasets used for baselines
        and drift comparison.

        Yields:
            :class:`~fiddler.entities.Dataset`: Dataset objects containing metadata and data access methods.
                    Each dataset represents a collection of events published to the model.

        Example:
            # List all datasets for the model
            for dataset in model.datasets:
                print(f"Dataset: {dataset.name}")
                print(f"  Environment: {dataset.environment}")
                print(f"  Size: {dataset.size} events")
                print(f"  Created: {dataset.created_at}")

            # Find specific dataset
            baseline_datasets = [
                ds for ds in model.datasets
                if ds.environment == EnvType.PRE_PRODUCTION
            ]
            print(f"Found {len(baseline_datasets)} baseline datasets")

        Note:
            This includes both production event data and named pre-production datasets.
            Use the Dataset objects to download data, analyze distributions, or
            set up baseline comparisons for drift detection.
        """
        from fiddler.entities.dataset import (  # pylint: disable=import-outside-toplevel
            Dataset,
        )

        assert self.id is not None

        yield from Dataset.list(model_id=self.id)

    @property
    def baselines(self) -> Iterator[Baseline]:
        """Get all baselines configured for this model.

        Returns an iterator over all baseline configurations used for drift detection
        and performance monitoring. Baselines define reference distributions and
        metrics for comparison with production data.

        Yields:
            :class:`~fiddler.entities.Baseline`: Baseline objects containing configuration and reference data.
                     Each baseline defines how drift and performance should be measured
                     against historical or reference datasets.

        Example:
            # List all baselines
            for baseline in model.baselines:
                print(f"Baseline: {baseline.name}")
                print(f"  Type: {baseline.type}")  # STATIC or ROLLING
                print(f"  Dataset: {baseline.dataset_name}")
                print(f"  Created: {baseline.created_at}")

            # Find production baseline
            prod_baselines = [
                bl for bl in model.baselines
                if "production" in bl.name.lower()
            ]

            # Use baseline for drift comparison
            if prod_baselines:
                baseline = prod_baselines[0]
                drift_metrics = baseline.compute_drift(recent_data)

        Note:
            Baselines are essential for drift detection and alerting. They define
            the "normal" behavior against which production data is compared.
            Static baselines use fixed reference data, while rolling baselines
            update automatically with recent data.
        """
        from fiddler.entities.baseline import (  # pylint: disable=import-outside-toplevel
            Baseline,
        )

        assert self.id is not None

        yield from Baseline.list(model_id=self.id)

    @cached_property
    @handle_api_error
    def deployment(self) -> ModelDeployment:
        """Fetch model deployment instance of this model.

        Returns:
            :class:`~fiddler.entities.ModelDeployment`: The deployment configuration for this model.
        """
        assert self.id is not None

        return ModelDeployment.of(model_id=self.id)

    @classmethod
    @handle_api_error
    def from_data(  # pylint: disable=too-many-arguments, too-many-locals
        cls,
        source: pd.DataFrame | Path | str,
        name: str,
        project_id: UUID | str,
        spec: ModelSpec | None = None,
        version: str | None = None,
        input_type: str = ModelInputType.TABULAR,
        task: str = ModelTask.NOT_SET,
        task_params: ModelTaskParams | None = None,
        description: str | None = None,
        event_id_col: str | None = None,
        event_ts_col: str | None = None,
        event_ts_format: str | None = None,
        xai_params: XaiParams | None = None,
        max_cardinality: int | None = None,
        sample_size: int | None = None,
    ) -> Model:
        """Create a Model instance with automatic schema generation from data.

        This is the most convenient way to create models when you have training data
        or representative samples. The method automatically analyzes the data to
        generate appropriate schema (column types) and spec (column roles) definitions.

        Args:
            source: Data source for schema generation. Can be:
                   - pandas.DataFrame: Direct data analysis
                   - Path/str: File path (.csv, .parquet, .json supported)
                   The data should be representative of your model's inputs/outputs.
            name: Model name, must be unique within the project version.
                 Use descriptive names like "fraud_detector_v1" or "churn_model".
            project_id: UUID or string identifier of the parent project.
            spec: Optional :class:`~fiddler.schemas.ModelSpec` defining column roles. If None, automatic
                 detection attempts to identify inputs, outputs, and targets
                 based on column names and data patterns.
            version: Model version identifier. If None, defaults to "v1".
                    Use semantic versioning like "v1.0", "v2.1", etc.
            input_type: :class:`~fiddler.constants.ModelInputType` - Type of input data the model processes.
                       - TABULAR: Structured/tabular data (default)
                       - TEXT: Natural language text data
                       - MIXED: Combination of structured and unstructured data
            task: :class:`~fiddler.constants.ModelTask` - Machine learning task type:
                 - BINARY_CLASSIFICATION: Binary classification (0/1, True/False)
                 - MULTICLASS_CLASSIFICATION: Multi-class classification
                 - REGRESSION: Continuous value prediction
                 - RANKING: Ranking/recommendation tasks
                 - LLM: Large language model tasks
                 - NOT_SET: Task not specified (default)
            task_params: :class:`~fiddler.schemas.ModelTaskParams` - Task-specific parameters:
                        - binary_classification_threshold: Decision threshold (0.5)
                        - target_class_order: Class label ordering
                        - group_by: Column for ranking model grouping
                        - top_k: Top-k evaluation for ranking
            description: Human-readable description of the model's purpose,
                        training approach, or other relevant information.
            event_id_col: Column name for unique event identifiers. Used for
                         tracking individual predictions and enabling updates.
            event_ts_col: Column name for event timestamps. Used for time-based
                         analysis, drift detection, and temporal monitoring.
            event_ts_format: Timestamp format string for parsing event_ts_col.
                           Examples: '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'
            xai_params: :class:`~fiddler.schemas.XaiParams` - Explainability configuration including explanation methods
                       and custom feature definitions.
            max_cardinality: Maximum unique values to consider a column categorical.
                           Columns with more unique values are treated as continuous.
                           Default is typically 100-1000 depending on data size.
            sample_size: Number of rows to sample for schema generation. Useful
                        for large datasets to speed up analysis. If None, uses
                        entire dataset (up to reasonable limits).

        Returns:
            :class:`~fiddler.entities.Model`: A new Model instance with automatically generated schema and spec.
                  The model is not yet created on the platform - call .create() to persist.

        Raises:
            ValueError: If the data source is invalid or cannot be processed.
            FileNotFoundError: If source is a file path that doesn't exist.
            ValidationError: If the generated schema/spec is invalid.

        Example:
            import pandas as pd

            # Create from DataFrame
            df = pd.DataFrame({
                'age': [25, 35, 45, 55],
                'income': [30000, 50000, 70000, 90000],
                'credit_score': [650, 700, 750, 800],
                'approved': [0, 1, 1, 1],  # target
                'prediction': [0.2, 0.8, 0.9, 0.95],  # model output
                'prediction_score': [0.2, 0.8, 0.9, 0.95]  # alternative output
            })

            model = Model.from_data(
                source=df,
                name="credit_approval_v1",
                project_id=project.id,
                task=ModelTask.BINARY_CLASSIFICATION,
                description="Credit approval model trained on 2024 data",
                event_id_col="application_id",  # if present in real data
                event_ts_col="timestamp"        # if present in real data
            )

            # Review generated schema
            print(f"Columns detected: {len(model.schema.columns)}")
            for col in model.schema.columns:
                print(f"  {col.name}: {col.data_type}")

            # Review generated spec
            print(f"Inputs: {model.spec.inputs}")
            print(f"Outputs: {model.spec.outputs}")
            print(f"Targets: {model.spec.targets}")

            # Create on platform
            model.create()

            # Create from file
            model = Model.from_data(
                source="training_data.csv",
                name="file_based_model",
                project_id=project.id,
                task=ModelTask.REGRESSION,
                sample_size=10000  # Sample large files
            )

        Note:
            The automatic schema generation uses heuristics to detect column types
            and roles. Review the generated schema and spec before calling .create()
            to ensure they match your model's actual interface. You can modify the
            schema and spec after creation if needed.
        """

        resp_obj = ModelGenerator(
            source=source,
            spec=spec,
        ).generate(max_cardinality=max_cardinality, sample_size=sample_size)

        return Model(
            name=name,
            version=version,
            schema=resp_obj.schema_,
            spec=resp_obj.spec,
            project_id=project_id,
            input_type=input_type,
            task=task,
            task_params=task_params,
            description=description,
            event_id_col=event_id_col,
            event_ts_col=event_ts_col,
            event_ts_format=event_ts_format,
            xai_params=xai_params,
        )

    @handle_api_error
    def delete(self) -> Job:
        """
        Delete a model and it's associated resources.

        :return: model deletion job instance
        """
        assert self.id is not None
        response = self._client().delete(url=self._get_url(id_=self.id))

        job_compact = JobCompactResp(**response.json()['data']['job'])
        return Job.get(id_=job_compact.id)

    def remove_column(self, column_name: str, missing_ok: bool = True) -> None:
        """
        Remove a column from the model schema and spec

        This method is only to modify model object before creating and
        will not save the model on Fiddler Platform. After making
        changes to the model instance, call `.create()` to add the model
        to Fiddler Platform.

        :param column_name: Column name to be removed
        :param missing_ok: If True, do not raise an error if the column is not found
        :return: None

        :raises KeyError: If the column name is not found and missing_ok is False
        """
        try:
            del self.schema[column_name]
        except KeyError as e:
            if not missing_ok:
                raise e
        self.spec.remove_column(column_name)

    @handle_api_error
    def publish(
        self,
        source: builtins.list[dict[str, Any]] | str | Path | pd.DataFrame,
        environment: EnvType = EnvType.PRODUCTION,
        dataset_name: str | None = None,
        update: bool = False,
    ) -> builtins.list[UUID] | Job:
        """Publish data to the model for monitoring and analysis.

        Uploads prediction events, training data, or reference datasets to Fiddler
        for monitoring, drift detection, and performance analysis. This is how you
        send your model's real-world data to the platform.

        Args:
            source: Data to publish. Supported formats:
                   - **File path (str/Path)**: CSV or Parquet files.
                     Best for large datasets and batch uploads.
                   - **DataFrame**: Pandas DataFrame with prediction events.
                     Good for programmatic uploads and real-time data.
                   - **List of dicts**: Individual events as dictionaries.
                     Perfect for streaming/real-time publishing (max 1000 events).
                     Each dict should match the model's schema.
            environment: :class:`~fiddler.constants.EnvType` - Data environment type:
                        - **PRODUCTION**: Live production prediction data.
                          Used for real-time monitoring and alerting.
                        - **PRE_PRODUCTION**: Training, validation, or baseline data.
                          Used for drift comparison and model evaluation.
            dataset_name: Name for the dataset when using PRE_PRODUCTION environment.
                         Creates a named dataset for baseline comparisons.
                         Not used for PRODUCTION data.
            update: Whether these events update previously published data.
                   Set to True when republishing corrected predictions or
                   adding ground truth labels to existing events.

        Returns:
            - **list[UUID]**: Event IDs when source is list of dicts or DataFrame.
              Use these IDs to reference specific events later.
            - :class:`~fiddler.entities.Job`: Async job object when source is a file path.
              Use job.wait() to wait for completion or check job.status.

        Raises:
            ValidationError: If the data doesn't match the model's schema or
                           contains invalid values.
            ApiError: If there's an error uploading the data to Fiddler.
            ValueError: If the source format is unsupported or parameters
                       are incompatible (e.g., dataset_name with PRODUCTION).

        Example:
            # Publish production events from DataFrame
            import pandas as pd
            prod_df = pd.DataFrame({
                'age': [30, 25, 45],
                'income': [60000, 45000, 80000],
                'prediction': [0.8, 0.3, 0.9],
                'timestamp': ['2024-01-01 10:00:00', '2024-01-01 11:00:00', '2024-01-01 12:00:00']
            })

            # Returns list of event UUIDs
            event_ids = model.publish(
                source=prod_df,
                environment=EnvType.PRODUCTION
            )
            print(f"Published {len(event_ids)} events")

            # Publish baseline data for drift comparison
            baseline_df = pd.read_csv("training_data.csv")
            job = model.publish(
                source="training_data.csv",  # File path
                environment=EnvType.PRE_PRODUCTION,
                dataset_name="training_baseline_2024"
            )
            job.wait()  # Wait for upload to complete
            print(f"Baseline upload status: {job.status}")

            # Publish real-time streaming events
            events = [
                {
                    'age': 35,
                    'income': 70000,
                    'prediction': 0.75,
                    'event_id': 'pred_001',
                    'timestamp': '2024-01-01 13:00:00'
                },
                {
                    'age': 28,
                    'income': 55000,
                    'prediction': 0.45,
                    'event_id': 'pred_002',
                    'timestamp': '2024-01-01 13:01:00'
                }
            ]
            event_ids = model.publish(source=events)
            print(f"Published {len(events)} streaming events")

            # Update existing events with ground truth
            corrected_events = [
                {
                    'event_id': 'pred_001',
                    'ground_truth': 1,  # Actual outcome
                    'timestamp': '2024-01-01 13:00:00'
                }
            ]
            model.publish(source=corrected_events, update=True)

        Important:
            - **Schema Validation**: All published data must match the model's schema.
              Column names, types, and value ranges are validated.
            - **Event IDs**: Include event_id_col if specified in model config for
              event tracking and updates.
            - **Timestamps**: Include event_ts_col for time-based analysis and drift detection.
            - **Batch Limits**: List of dicts is limited to 1000 events per call.
              Use files or multiple calls for larger datasets.

        Note:
            Production data publishing enables real-time monitoring, alerting, and
            drift detection. Pre-production data creates reference datasets for
            comparison and model evaluation.
        """
        logger.info('Model[%s/%s] - Publishing events', self.name, self.version)
        return self._event_publisher.publish(
            source=source,
            environment=environment,
            dataset_name=dataset_name,
            update=update,
        )

    def add_artifact(
        self,
        model_dir: str | Path,
        deployment_params: DeploymentParams | None = None,
    ) -> Job:
        """
        Upload and deploy model artifact.

        :param model_dir: Path to model artifact tar file
        :param deployment_params: Model deployment parameters
        :return: Async job instance
        """
        return self._artifact.add(
            model_dir=model_dir, deployment_params=deployment_params
        )

    def update_artifact(
        self,
        model_dir: str | Path,
        deployment_params: DeploymentParams | None = None,
    ) -> Job:
        """
        Update existing model artifact.

        :param model_dir: Path to model artifact tar file
        :param deployment_params: Model deployment parameters
        :return: Async job instance
        """
        return self._artifact.update(
            model_dir=model_dir, deployment_params=deployment_params
        )

    def download_artifact(
        self,
        output_dir: str | Path,
    ) -> None:
        """
        Download existing model artifact.

        :param output_dir: Path to download model artifact tar file
        """

        self._artifact.download(output_dir=output_dir)

    def add_surrogate(
        self,
        dataset_id: UUID | str,
        deployment_params: DeploymentParams | None = None,
    ) -> Job:
        """
        Add a new surrogate model

        :param dataset_id: Dataset to be used for generating surrogate model
        :param deployment_params: Model deployment parameters
        :return: Async job
        """
        job = self._surrogate.add(
            dataset_id=dataset_id, deployment_params=deployment_params
        )
        return job

    @handle_api_error
    def update_surrogate(
        self,
        dataset_id: UUID | str,
        deployment_params: DeploymentParams | None = None,
    ) -> Job:
        """
        Update an existing surrogate model

        :param dataset_id: Dataset to be used for generating surrogate model
        :param deployment_params: Model deployment parameters
        :return: Async job
        """
        job = self._surrogate.update(
            dataset_id=dataset_id, deployment_params=deployment_params
        )
        return job


@dataclass
class ModelCompact:
    """Lightweight model representation for listing and basic operations.

    A minimal model object containing only essential identifiers. Used by
    Model.list() to efficiently return model information without fetching
    full schema and configuration details.

    Attributes:
        id: Unique model identifier (UUID)
        name: Model name within the project
        version: Model version identifier, may be None for default version

    Example:
        # Get from listing
        models = list(Model.list(project_id=project.id))
        compact_model = models[0]

        # Access basic info
        print(f"Model: {compact_model.name} v{compact_model.version}")
        print(f"ID: {compact_model.id}")

        # Fetch full details when needed
        full_model = compact_model.fetch()
        print(f"Task: {full_model.task}")
        print(f"Schema: {len(full_model.schema.columns)} columns")
    """

    id: UUID
    name: str
    version: str | None = None

    def fetch(self) -> Model:
        """Fetch the complete Model instance.

        Retrieves the full Model object with all schema, spec, and configuration
        details from the Fiddler platform using this compact model's ID.

        Returns:
            :class:`~fiddler.entities.Model`: Complete model instance with all details and capabilities.

        Example:
            # From model listing
            compact = next(Model.list(project_id=project.id))

            # Get full model details
            full_model = compact.fetch()

            # Now can access full functionality
            full_model.publish(source=data)
            print(f"Input columns: {full_model.spec.inputs}")
        """
        return Model.get(id_=self.id)


class ModelCompactMixin:
    @property
    def model(self) -> ModelCompact:
        """Model instance"""
        response = getattr(self, '_resp', None)
        if not response or not hasattr(response, 'model'):
            raise AttributeError(
                'This property is available only for objects generated from API '
                'response.'
            )

        return ModelCompact(
            id=response.model.id,
            name=response.model.name,
            version=response.model.version,
        )
