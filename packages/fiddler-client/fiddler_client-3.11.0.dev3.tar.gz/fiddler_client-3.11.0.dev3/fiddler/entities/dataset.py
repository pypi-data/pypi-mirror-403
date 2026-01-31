"""
Dataset entity for managing and organizing data within Fiddler models.

The Dataset class represents collections of data that have been published to models
in the Fiddler platform. Datasets serve as the foundation for model monitoring,
drift detection, baseline creation, and performance analysis.

Key Concepts:
    - **Data Organization**: Datasets group related data records for analysis
    - **Environment Types**: Production vs. pre-production data separation
    - **Model Association**: Each dataset belongs to a specific model
    - **Baseline Creation**: Datasets serve as reference data for drift detection
    - **Time-based Analysis**: Support for temporal data analysis and monitoring

Data Lifecycle:
    1. **Data Publishing**: Publish data to models using Model.publish()
    2. **Dataset Creation**: Fiddler automatically creates dataset records
    3. **Baseline Setup**: Use datasets to create baselines for monitoring
    4. **Drift Detection**: Compare new data against dataset baselines
    5. **Analysis**: Download and analyze dataset contents
    6. **Monitoring**: Track data quality and distribution changes

Environment Types:
    - **PRE_PRODUCTION**: Training, validation, and baseline data
    - **PRODUCTION**: Live prediction data for real-time monitoring

Example:
    # Get dataset for a model
    dataset = Dataset.from_name(
        name="training_baseline",
        model_id=model.id
    )
    print(f"Dataset: {dataset.name} ({dataset.row_count} rows)")

    # List all datasets for a model
    for dataset in Dataset.list(model_id=model.id):
        print(f"Dataset: {dataset.name} - {dataset.row_count} rows")

    # Use dataset for baseline creation
    baseline = Baseline.create_from_dataset(
        dataset_id=dataset.id,
        name="training_baseline"
    )

Note:
    Datasets are automatically created when data is published to models.
    They cannot be created directly but are managed through the Model.publish()
    workflow. Dataset names must be unique within a model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator
from uuid import UUID

from fiddler.constants.dataset import EnvType
from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.entities.project import ProjectCompactMixin
from fiddler.schemas.dataset import DatasetResp
from fiddler.schemas.filter_query import OperatorType, QueryCondition, QueryRule
from fiddler.utils.helpers import raise_not_found


class Dataset(BaseEntity, ProjectCompactMixin):
    """Represents a dataset containing data published to a Fiddler model.

    A Dataset is a collection of data records that have been published to a specific
    model in the Fiddler platform. Datasets are automatically created when data is
    published using Model.publish() and serve as the foundation for monitoring,
    drift detection, and baseline creation.

    Key Features:
        - **Data Collection**: Organized storage of model input/output data
        - **Environment Separation**: Distinct handling of production vs. pre-production data
        - **Baseline Source**: Reference data for drift detection and monitoring
        - **Analysis Support**: Data download and statistical analysis capabilities
        - **Model Integration**: Tight coupling with specific models for context

    Dataset Characteristics:
        - **Automatic Creation**: Created by Model.publish() operations
        - **Model-Scoped**: Each dataset belongs to exactly one model
        - **Named Collections**: Unique names within a model for identification
        - **Row Tracking**: Automatic counting of data records
        - **Environment Typed**: Classified as production or pre-production data

    Attributes:
        name (str): Dataset name, unique within the model.
        model_id (UUID | str): Identifier of the parent model.
        project_id (UUID | str): Identifier of the parent project.
        row_count (int, optional): Number of data records in the dataset.
        id (UUID, optional): Unique dataset identifier, assigned by server.

    Example:
        # Retrieve a specific dataset
        dataset = Dataset.from_name(
            name="training_data_v1",
            model_id=model.id
        )
        print(f"Dataset: {dataset.name}")
        print(f"Rows: {dataset.row_count}")
        print(f"Model: {dataset.model_id}")

        # List all datasets for a model
        datasets = list(Dataset.list(model_id=model.id))
        print(f"Found {len(datasets)} datasets")

        # Find datasets by characteristics
        large_datasets = [
            ds for ds in Dataset.list(model_id=model.id)
            if ds.row_count and ds.row_count > 10000
        ]

    Note:
        Datasets cannot be created directly through the Dataset class. They are
        automatically created when data is published to models using Model.publish().
        Use the Dataset class for retrieval, listing, and analysis operations.
    """
    def __init__(self, name: str, model_id: str | UUID, project_id: UUID | str) -> None:
        """Initialize a Dataset instance.

        Creates a dataset object representing data published to a model. This constructor
        is typically used internally when deserializing API responses rather than for
        direct dataset creation.

        Args:
            name: Dataset name, must be unique within the model.
                 Should be descriptive of the data contents or purpose.
            model_id: Identifier of the model this dataset belongs to.
                     Can be provided as UUID object or string representation.
            project_id: Identifier of the parent project.
                       Can be provided as UUID object or string representation.

        Example:
            # Internal usage - typically not called directly
            dataset = Dataset(
                name="training_baseline_v1",
                model_id="550e8400-e29b-41d4-a716-446655440000",
                project_id="660e8400-e29b-41d4-a716-446655440000"
            )

        Note:
            Datasets are typically retrieved using Dataset.get(), Dataset.from_name(),
            or Dataset.list() rather than created directly. Direct creation is mainly
            used internally by the Fiddler client.
        """
        self.model_id = model_id
        self.project_id = project_id
        self.name = name
        self.row_count: int | None = None

        self.id: UUID | None = None  # pylint: disable=invalid-name

        # Deserialized response object
        self._resp: DatasetResp | None = None

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get model resource/item url."""
        url = '/v3/environments'
        return url if not id_ else f'{url}/{id_}'

    @classmethod
    def _from_dict(cls, data: dict) -> Dataset:
        """Build entity object from the given dictionary."""

        # Deserialize the response
        resp_obj = DatasetResp(**data)

        # Initialize
        instance = cls(
            name=resp_obj.name,
            model_id=resp_obj.model.id,
            project_id=resp_obj.project.id,
        )

        # Add remaining fields
        fields = [
            'id',
            'row_count',
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj

        return instance

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str) -> Dataset:
        """Retrieve a dataset by its unique identifier.

        Fetches a dataset from the Fiddler platform using its UUID. This is the most
        direct way to retrieve a dataset when you know its ID.

        Args:
            id_: The unique identifier (UUID) of the dataset to retrieve.
                Can be provided as a UUID object or string representation.

        Returns:
            :class:`~fiddler.entities.Dataset`: The dataset instance with all metadata and row count information.

        Raises:
            NotFound: If no dataset exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get dataset by UUID
            dataset = Dataset.get(id_="550e8400-e29b-41d4-a716-446655440000")
            print(f"Retrieved dataset: {dataset.name}")
            print(f"Rows: {dataset.row_count}")
            print(f"Model: {dataset.model_id}")

            # Use dataset for analysis
            if dataset.row_count and dataset.row_count > 1000:
                print("Large dataset suitable for baseline creation")

        Note:
            This method makes an API call to fetch the latest dataset state from the server.
            The returned dataset instance reflects the current state in Fiddler.
        """
        response = cls._client().get(url=cls._get_url(id_=id_))
        return cls._from_response(response=response)

    @classmethod
    @handle_api_error
    def from_name(cls, name: str, model_id: UUID | str) -> Dataset:
        """Retrieve a dataset by name within a specific model.

        Finds and returns a dataset using its name and model context. Dataset names
        are unique within a model, making this a reliable lookup method when you
        know both the dataset name and model ID.

        Args:
            name: The name of the dataset to retrieve. Dataset names are unique
                 within a model and are case-sensitive.
            model_id: The identifier of the model containing the dataset.
                     Can be provided as UUID object or string representation.

        Returns:
            :class:`~fiddler.entities.Dataset`: The dataset instance matching the specified name and model.

        Raises:
            NotFound: If no dataset exists with the specified name in the given model.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get dataset by name for a specific model
            dataset = Dataset.from_name(
                name="training_baseline",
                model_id=model.id
            )
            print(f"Found dataset: {dataset.name}")
            print(f"Rows: {dataset.row_count}")

            # Get validation dataset
            val_dataset = Dataset.from_name(
                name="validation_set_v2",
                model_id=model.id
            )

            # Use for baseline creation
            baseline = Baseline.create_from_dataset(
                dataset_id=dataset.id,
                name="training_baseline"
            )

        Note:
            Dataset names are case-sensitive and must match exactly. This method
            is useful when you know the dataset name from configuration or when
            working with named datasets created during model training workflows.
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
            raise_not_found('Dataset not found for the given identifier')

        return cls._from_dict(data=response.json()['data']['items'][0])

    @classmethod
    @handle_api_error
    def list(cls, model_id: UUID | str) -> Iterator[Dataset]:
        """List all pre-production datasets for a specific model.

        Retrieves all datasets that have been published to a model in the pre-production
        environment. These datasets are typically used for baselines, training data
        analysis, and validation purposes.

        Args:
            model_id: The identifier of the model to list datasets for.
                     Can be provided as UUID object or string representation.

        Yields:
            :class:`~fiddler.entities.Dataset`: Dataset instances for all pre-production datasets in the model.

        Raises:
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # List all datasets for a model
            for dataset in Dataset.list(model_id=model.id):
                print(f"Dataset: {dataset.name}")
                print(f"  Rows: {dataset.row_count}")
                print(f"  ID: {dataset.id}")

            # Convert to list for analysis
            datasets = list(Dataset.list(model_id=model.id))
            print(f"Found {len(datasets)} datasets")

            # Find datasets by characteristics
            large_datasets = [
                ds for ds in Dataset.list(model_id=model.id)
                if ds.row_count and ds.row_count > 10000
            ]
            print(f"Large datasets: {len(large_datasets)}")

            # Get dataset summary statistics
            total_rows = sum(
                ds.row_count or 0
                for ds in Dataset.list(model_id=model.id)
            )
            print(f"Total rows across all datasets: {total_rows}")

        Note:
            This method returns an iterator for memory efficiency and only includes
            pre-production datasets. Production data is handled separately through
            the monitoring system. Convert to a list with list(Dataset.list(...))
            if you need to iterate multiple times.
        """
        params: dict[str, Any] = {'type': EnvType.PRE_PRODUCTION.value}
        url = f'/v3/models/{model_id}/environments'
        for dataset in cls._paginate(url=url, params=params):
            yield cls._from_dict(data=dataset)


@dataclass
class DatasetCompact:
    """Lightweight dataset representation for listing and basic operations.

    A minimal dataset object containing only essential identifiers. Used by
    various operations to efficiently reference datasets without fetching
    full dataset details and metadata.

    This class provides a memory-efficient way to work with dataset references
    when you don't need the full dataset functionality but want to access
    basic information or fetch the complete dataset when needed.

    Attributes:
        id (UUID): Unique dataset identifier
        name (str): Dataset name within the model

    Example:
        # From dataset references in other entities
        baseline = Baseline.get(id_="baseline-uuid")
        dataset_ref = baseline.dataset  # Returns DatasetCompact

        # Access basic info
        print(f"Dataset: {dataset_ref.name}")
        print(f"ID: {dataset_ref.id}")

        # Fetch full details when needed
        full_dataset = dataset_ref.fetch()
        print(f"Rows: {full_dataset.row_count}")
        print(f"Model: {full_dataset.model_id}")

    Note:
        DatasetCompact objects are typically returned by other entities that
        reference datasets. Use .fetch() to get the complete Dataset instance
        when you need full functionality like row counts or model information.
    """
    id: UUID
    name: str

    def fetch(self) -> Dataset:
        """Fetch the complete Dataset instance.

        Retrieves the full Dataset object with all metadata, row counts, and
        model associations from the Fiddler platform using this compact dataset's ID.

        Returns:
            :class:`~fiddler.entities.Dataset`: Complete dataset instance with all details and capabilities.

        Example:
            # From dataset reference
            compact = baseline.dataset

            # Get full dataset details
            full_dataset = compact.fetch()

            # Now can access full functionality
            print(f"Dataset has {full_dataset.row_count} rows")
            print(f"Belongs to model: {full_dataset.model_id}")
        """
        return Dataset.get(id_=self.id)


class DatasetCompactMixin:
    @property
    def dataset(self) -> DatasetCompact | None:
        """Get the dataset reference for this entity.

        Returns a lightweight DatasetCompact object containing the dataset
        information associated with this entity, or None if this entity
        references production data (which is not exposed as datasets).

        Returns:
            :class:`~fiddler.entities.DatasetCompact` | None: Lightweight dataset reference with id and name,
                  or None if the entity references production data.

        Raises:
            AttributeError: If this property is accessed on an object not generated
                          from an API response, or if the response doesn't contain dataset information.

        Example:
            # Get dataset reference from a baseline
            baseline = Baseline.get(id_="baseline-uuid")
            dataset_ref = baseline.dataset
            if dataset_ref:
                print(f"Baseline uses dataset: {dataset_ref.name}")
                full_dataset = dataset_ref.fetch()
                print(f"Dataset has {full_dataset.row_count} rows")
            else:
                print("Baseline references production data")

        Note:
            This property returns None for entities that reference production data,
            as production data is not exposed through the Dataset API. Only
            pre-production datasets are accessible through this interface.
        """
        response = getattr(self, '_resp', None)
        if not response or not hasattr(response, 'dataset'):
            raise AttributeError(
                'This property is available only for objects generated from API '
                'response.'
            )

        if response.dataset.type == EnvType.PRODUCTION:
            return None

        return DatasetCompact(id=response.dataset.id, name=response.dataset.name)
