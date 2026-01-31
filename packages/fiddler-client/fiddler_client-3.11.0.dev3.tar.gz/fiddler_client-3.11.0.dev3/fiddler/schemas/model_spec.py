from typing import List, Union

from pydantic.v1 import BaseModel, Field

from fiddler.schemas.custom_features import (
    Enrichment,
    ImageEmbedding,
    Multivariate,
    TextEmbedding,
    VectorFeature,
)


class ModelSpec(BaseModel):
    """Defines how model columns are categorized and used along with model task configuration.

    ModelSpec provides a comprehensive specification of how different columns in your
    model's data should be interpreted and used. It categorizes columns into inputs,
    outputs, targets, decisions, and metadata, and allows for custom feature definitions
    that enhance model monitoring and analysis capabilities.

    This specification is crucial for Fiddler to understand your model's structure,
    enabling proper monitoring, drift detection, bias analysis, and explainability
    features. It acts as the contract between your model and Fiddler's monitoring
    infrastructure.

    Attributes:
        schema_version: Version of the specification format (currently 1)
        inputs: List of feature column names used as model inputs
        outputs: List of prediction column names produced by the model
        targets: List of ground truth label column names for supervised learning
        decisions: List of decision column names for decision-based models
        metadata: List of metadata column names (not used for training/prediction)
        custom_features: List of custom feature definitions for enhanced monitoring

    Examples:
        Creating a basic model spec for classification:

        spec = ModelSpec(
            inputs=["age", "income", "credit_score"],
            outputs=["prediction", "probability"],
            targets=["approved"],
            metadata=["customer_id", "timestamp"]
        )

        Creating a spec with custom features:

        from fiddler.schemas.custom_features import Multivariate, TextEmbedding

        spec = ModelSpec(
            inputs=["user_clicks", "session_time", "review_text_embedding"],
            outputs=["recommendation_score"],
            targets=["user_rating"],
            metadata=["user_id", "session_id"],
            custom_features=[
                Multivariate(
                    name="user_behavior",
                    columns=["user_clicks", "session_time"],
                    n_clusters=5
                ),
                TextEmbedding(
                    name="review_clusters",
                    column="review_text_embedding",
                    source_column="review_text",
                    n_clusters=8
                )
            ]
        )

        Creating a spec for ranking models:

        ranking_spec = ModelSpec(
            inputs=["query_features", "doc_features", "relevance_score"],
            outputs=["ranking_score"],
            targets=["click_through"],
            decisions=["final_ranking"],
            metadata=["query_id", "doc_id"]
        )
    """

    schema_version: int = 1
    """Schema version"""

    inputs: List[str] = Field(default_factory=list)
    """Feature columns"""

    outputs: List[str] = Field(default_factory=list)
    """Prediction columns"""

    targets: List[str] = Field(default_factory=list)
    """Label columns"""

    decisions: List[str] = Field(default_factory=list)
    """Decisions columns"""

    metadata: List[str] = Field(default_factory=list)
    """Metadata columns"""

    custom_features: List[
        Union[Multivariate, VectorFeature, TextEmbedding, ImageEmbedding, Enrichment]
    ] = Field(default_factory=list)
    """Custom feature definitions"""

    def remove_column(self, column_name: str) -> None:
        """Remove a column name from spec if it exists."""
        column_lists = [
            self.inputs,
            self.outputs,
            self.targets,
            self.decisions,
            self.metadata,
        ]

        for cols in column_lists:
            if column_name in cols:  # pylint: disable=unsupported-membership-test
                cols.remove(column_name)  # pylint: disable=no-member
                break
