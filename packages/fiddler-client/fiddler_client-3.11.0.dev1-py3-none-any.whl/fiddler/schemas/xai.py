from typing import Dict, Optional, Union
from uuid import UUID

from pydantic.v1 import Field

from fiddler.constants.dataset import EnvType
from fiddler.schemas.base import BaseModel


class RowDataSource(BaseModel):
    """Data source for explainability analysis using a single row of data.

    RowDataSource allows you to perform explainability analysis on a specific
    data row by providing the row data directly. This is useful when you want
    to explain a particular prediction or analyze feature importance for a
    specific instance without referencing stored data.

    This data source type is ideal for real-time explanations, ad-hoc analysis,
    or when you have specific data points that you want to analyze independently
    of your stored datasets.

    Attributes:
        source_type: Fixed as 'ROW' to identify this data source type
        row: Dictionary containing the data values for explanation analysis

    Examples:
        Creating a row data source for a loan application:

        row_source = RowDataSource(
            row={
                "age": 35,
                "income": 75000,
                "credit_score": 720,
                "employment_years": 8,
                "loan_amount": 250000
            }
        )

        Creating a row data source for image classification:

        image_row_source = RowDataSource(
            row={
                "image_features": [0.1, 0.5, 0.3, ...],
                "metadata": "product_image_001.jpg",
                "category": "electronics"
            }
        )
    """
    source_type = 'ROW'
    row: Dict


class EventIdDataSource(BaseModel):
    """Data source for explainability analysis using a specific event ID.

    EventIdDataSource allows you to perform explainability analysis on a specific
    event that has been previously logged to Fiddler. This is useful when you want
    to explain predictions for events that are already stored in your environment,
    enabling you to analyze historical predictions and their explanations.

    This data source type is ideal for investigating specific incidents, analyzing
    historical predictions, or performing post-hoc analysis on logged events.

    Attributes:
        source_type: Fixed as 'EVENT_ID' to identify this data source type
        event_id: Unique identifier of the event to analyze
        env_id: Environment/dataset ID where the event is stored
        env_type: Type of environment (PRODUCTION, VALIDATION, etc.)

    Examples:
        Creating an event data source for production analysis:

        event_source = EventIdDataSource(
            event_id="evt_12345abcdef",
            env_id="prod_dataset_uuid",
            env_type=EnvType.PRODUCTION
        )

        Creating an event data source for validation analysis:

        validation_event_source = EventIdDataSource(
            event_id="validation_event_789",
            env_id="validation_dataset_uuid",
            env_type=EnvType.VALIDATION
        )
    """
    source_type = 'EVENT_ID'
    event_id: str
    env_id: Optional[Union[str, UUID]] = Field(alias='dataset_id')
    env_type: EnvType


class DatasetDataSource(BaseModel):
    """Data source for explainability analysis using a sample from a dataset.

    DatasetDataSource allows you to perform explainability analysis on a random
    sample of data from a specified environment/dataset. This is useful for
    understanding general model behavior, analyzing feature importance patterns
    across multiple instances, or getting representative explanations.

    This data source type is ideal for exploratory analysis, understanding overall
    model behavior, or when you want to analyze explanations across a representative
    sample rather than specific instances.

    Attributes:
        source_type: Fixed as 'ENVIRONMENT' to identify this data source type
        env_type: Type of environment to sample from
        num_samples: Number of samples to use for analysis (optional)
        env_id: Environment/dataset ID to sample from (optional)

    Examples:
        Creating a dataset data source for production sampling:

        dataset_source = DatasetDataSource(
            env_type="PRODUCTION",
            num_samples=100,
            env_id="prod_dataset_uuid"
        )

        Creating a dataset data source for validation analysis:

        validation_source = DatasetDataSource(
            env_type="VALIDATION",
            num_samples=50
        )

        Creating a dataset data source with default sampling:

        default_source = DatasetDataSource(
            env_type="PRODUCTION"
        )
    """
    source_type = 'ENVIRONMENT'
    env_type: str
    num_samples: Optional[int]
    env_id: Optional[Union[str, UUID]] = Field(alias='dataset_id')
