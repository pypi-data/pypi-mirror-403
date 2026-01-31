# pylint: disable=E0213
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar

from pydantic.v1 import BaseModel, validator

from fiddler.configs import DEFAULT_NUM_CLUSTERS, DEFAULT_NUM_TAGS
from fiddler.constants.model import CustomFeatureType

CustomFeatureTypeVar = TypeVar('CustomFeatureTypeVar', bound='CustomFeature')


class CustomFeature(BaseModel):
    """Base class for all custom feature types in Fiddler models.

    CustomFeature provides the foundation for creating specialized feature types
    that enhance model monitoring and analysis. Custom features allow you to define
    derived metrics, embeddings, and enrichments that extend beyond basic model
    inputs and outputs for advanced drift detection and analysis.

    This is an abstract base class that should not be instantiated directly.
    Instead, use one of its concrete subclasses: Multivariate, VectorFeature,
    TextEmbedding, ImageEmbedding, or Enrichment.

    Attributes:
        name: The unique name identifier for this custom feature
        type: The specific type of custom feature (discriminated by subclass)

    Examples:
        Creating a multivariate feature from multiple columns:

        feature = CustomFeature.from_columns(
            custom_name="user_behavior_cluster",
            cols=["clicks", "views", "time_spent"],
            n_clusters=5
        )

        Creating a custom feature from a dictionary:

        feature_dict = {
            "name": "text_sentiment",
            "type": "FROM_TEXT_EMBEDDING",
            "column": "embedding_col",
            "source_column": "review_text"
        }
        feature = CustomFeature.from_dict(feature_dict)
    """
    name: str
    type: Any

    class Config:
        allow_mutation = False
        use_enum_values = True
        discriminator = 'type'

    @classmethod
    def from_columns(
        cls, custom_name: str, cols: List[str], n_clusters: int = DEFAULT_NUM_CLUSTERS
    ) -> 'Multivariate':
        return Multivariate(
            name=custom_name,
            columns=cols,
            n_clusters=n_clusters,
        )

    @classmethod
    def from_dict(cls: Type[CustomFeatureTypeVar], deserialized_json: dict) -> Any:
        feature_type = CustomFeatureType(deserialized_json['type'])
        if feature_type == CustomFeatureType.FROM_COLUMNS:
            return Multivariate.parse_obj(deserialized_json)
        if feature_type == CustomFeatureType.FROM_VECTOR:
            return VectorFeature.parse_obj(deserialized_json)
        if feature_type == CustomFeatureType.FROM_TEXT_EMBEDDING:
            return TextEmbedding.parse_obj(deserialized_json)
        if feature_type == CustomFeatureType.FROM_IMAGE_EMBEDDING:
            return ImageEmbedding.parse_obj(deserialized_json)
        if feature_type == CustomFeatureType.ENRICHMENT:
            return Enrichment.parse_obj(deserialized_json)

        raise ValueError(f'Unsupported feature type: {feature_type}')

    def to_dict(self) -> Dict[str, Any]:
        return_dict: Dict[str, Any] = {
            'name': self.name,
            'type': self.type.value,
        }
        if isinstance(self, Multivariate):
            return_dict['columns'] = self.columns
            return_dict['n_clusters'] = self.n_clusters
        elif isinstance(self, VectorFeature):
            return_dict['column'] = self.column
            return_dict['n_clusters'] = self.n_clusters
            if isinstance(self, (ImageEmbedding, TextEmbedding)):
                return_dict['source_column'] = self.source_column
                if isinstance(self, TextEmbedding):
                    return_dict['n_tags'] = self.n_tags
        elif isinstance(self, Enrichment):
            return_dict['columns'] = self.columns
            return_dict['enrichment'] = self.enrichment
            return_dict['config'] = self.config
        else:
            raise ValueError(f'Unsupported feature type: {self.type} {type(self)}')

        return return_dict


class Multivariate(CustomFeature):
    """Represents custom features derived from multiple columns using clustering analysis.

    Multivariate features combine multiple numeric columns into a single derived feature
    using k-means clustering algorithms. This enables monitoring of multivariate drift
    and detecting unusual combinations that might not be apparent when monitoring
    columns individually.

    The feature type is automatically set to CustomFeatureType.FROM_COLUMNS and uses
    clustering to group similar combinations of column values for drift detection.

    Attributes:
        type: Fixed as CustomFeatureType.FROM_COLUMNS for multivariate features
        n_clusters: Number of clusters to create (default: 5)
        centroids: Computed cluster centroids in embedded space (populated during training)
        columns: List of original column names from which this feature is derived
        monitor_components: Whether to monitor each column individually for drift

    Examples:
        Creating a user behavior multivariate feature:

        behavior_feature = Multivariate(
            name="user_engagement_cluster",
            columns=["page_views", "session_duration", "clicks"],
            n_clusters=8,
            monitor_components=True
        )

        Creating a system performance multivariate feature:

        perf_feature = Multivariate(
            name="system_health",
            columns=["cpu_usage", "memory_usage", "response_time"],
            n_clusters=5,
            monitor_components=False
        )
    """
    type: Literal['FROM_COLUMNS'] = CustomFeatureType.FROM_COLUMNS.value
    n_clusters: Optional[int] = DEFAULT_NUM_CLUSTERS
    centroids: Optional[List] = None
    columns: List[str]
    monitor_components: bool = False

    @validator('columns')
    def validate_columns(cls, value: List[str]) -> List[str]:  # noqa: N805
        if len(value) < 2:
            raise ValueError('Multivariate columns must be greater than 1')
        return value

    @validator('n_clusters')
    def validate_n_clusters(cls, value: int) -> int:  # noqa: N805
        if value < 0:
            raise ValueError('n_clusters must be greater than 0')
        return value


class VectorFeature(CustomFeature):
    """Represents custom features derived from a single vector column using clustering analysis.

    VectorFeature processes high-dimensional vector data (like embeddings or feature
    vectors) by applying k-means clustering to create discrete clusters that can be
    monitored for distribution changes over time. This is particularly useful for
    monitoring embedding drift in high-dimensional spaces.

    The feature type is automatically set to CustomFeatureType.FROM_VECTOR and creates
    meaningful groupings from vector data for drift detection and anomaly identification.

    Attributes:
        type: Fixed as CustomFeatureType.FROM_VECTOR for vector features
        n_clusters: Number of clusters to create (default: 5)
        centroids: Computed cluster centroids in embedded space (populated during training)
        column: The vector column name from which this feature is derived
        source_column: Optional original column if this feature is derived from an embedding

    Examples:
        Creating a feature from a general embedding column:

        vector_feature = VectorFeature(
            name="embedding_clusters",
            column="user_embedding",
            n_clusters=10
        )

        Creating a feature from model hidden states:

        hidden_feature = VectorFeature(
            name="hidden_state_clusters",
            column="model_hidden_layer",
            n_clusters=15,
            source_column="input_features"
        )
    """
    type: Literal['FROM_VECTOR'] = CustomFeatureType.FROM_VECTOR.value
    n_clusters: Optional[int] = DEFAULT_NUM_CLUSTERS
    centroids: Optional[List] = None
    column: str

    @validator('n_clusters')
    def validate_n_clusters(cls, value: int) -> int:  # noqa: N805
        if value < 0:
            raise ValueError('n_clusters must be greater than 0')
        return value


class TextEmbedding(VectorFeature):
    """Represents custom features derived from text embeddings with TF-IDF analysis.

    TextEmbedding extends VectorFeature to handle text-based embeddings with additional
    text-specific analysis capabilities. It combines vector clustering with TF-IDF
    analysis to provide both semantic clustering and keyword extraction for text data.

    The feature type is automatically set to CustomFeatureType.FROM_TEXT_EMBEDDING
    and uses clustering combined with TF-IDF summarization for drift computation.

    Attributes:
        type: Fixed as CustomFeatureType.FROM_TEXT_EMBEDDING for text embedding features
        source_column: Name of the original text column that generated the embedding
        n_tags: Number of tags (tokens) used in each cluster for TF-IDF summarization (default: 5)
        tf_idf: TF-IDF analysis results (populated during training)

    Examples:
        # Creating a text embedding feature for review analysis:

        text_feature = TextEmbedding(
            name="review_sentiment_clusters",
            column="review_embedding",
            source_column="review_text",
            n_clusters=8,
            n_tags=20
        )

        # Creating a feature for document classification:

        doc_feature = TextEmbedding(
            name="document_topic_clusters",
            column="doc_embedding",
            source_column="document_content",
            n_clusters=12,
            n_tags=15
        )
    """
    type: Literal['FROM_TEXT_EMBEDDING'] = CustomFeatureType.FROM_TEXT_EMBEDDING.value  # type: ignore
    source_column: str
    n_tags: Optional[int] = DEFAULT_NUM_TAGS
    tf_idf: Optional[Dict[str, List]] = None

    @validator('n_tags')
    def validate_n_tags(cls, value: int) -> int:  # noqa: N805
        if value < 0:
            raise ValueError('n_tags must be greater than 0')
        return value


class ImageEmbedding(VectorFeature):
    """Represents custom features derived from image embeddings for visual content analysis.

    ImageEmbedding extends VectorFeature to handle image-based embeddings, providing
    clustering analysis specifically designed for visual content. This feature type
    is used to monitor image models and detect visual drift in high-dimensional
    embedding spaces.

    The feature type is automatically set to CustomFeatureType.FROM_IMAGE_EMBEDDING
    and applies clustering to image embeddings for visual pattern analysis.

    Attributes:
        type: Fixed as CustomFeatureType.FROM_IMAGE_EMBEDDING for image embedding features
        source_column: Name of the original image column or identifier that generated the embedding

    Examples:
        Creating an image embedding feature for product photos:

        image_feature = ImageEmbedding(
            name="product_image_clusters",
            column="product_embedding",
            source_column="product_image_url",
            n_clusters=15
        )

        Creating a feature for medical image analysis:

        medical_feature = ImageEmbedding(
            name="xray_pattern_clusters",
            column="xray_embedding",
            source_column="xray_image_path",
            n_clusters=10
        )
    """
    type: Literal['FROM_IMAGE_EMBEDDING'] = CustomFeatureType.FROM_IMAGE_EMBEDDING.value  # type: ignore
    source_column: str


class Enrichment(CustomFeature):
    """Represents custom features derived from enrichment operations (Private Preview).

    Enrichment features apply external processing or analysis to existing columns
    to create derived insights. This can include operations like sentiment analysis,
    toxicity detection, entity extraction, SQL validation, JSON validation, or any
    custom transformation that adds value to the original data.

    The feature type is automatically set to CustomFeatureType.ENRICHMENT and enables
    domain-specific analysis through configurable enrichment operations.

    Attributes:
        type: Fixed as CustomFeatureType.ENRICHMENT for enrichment features
        columns: List of original column names from which this feature is derived
        enrichment: String identifier for the type of enrichment to be applied
        config: Dictionary containing configuration options for the enrichment

    Examples:
        # Creating a sentiment analysis enrichment:

        sentiment_enrichment = Enrichment(
            name="review_sentiment",
            columns=["review_text"],
            enrichment="sentiment_analysis",
            config={
                "model": "vader",
                "return_scores": True
            }
        )

        # Creating a SQL validation enrichment:

        sql_enrichment = Enrichment(
            name="sql_validation",
            columns=["query_string"],
            enrichment="sql_validation",
            config={
                "dialect": "postgresql",
                "strict": True
            }
        )

        # Creating a JSON validation enrichment:

        json_enrichment = Enrichment(
            name="json_validation",
            columns=["json_string"],
            enrichment="json_validation",
            config={
                "strict": True,
                "validation_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "prop_1": {"type": "number"}
                    },
                    "required": ["prop_1"],
                    "additionalProperties": False
                }
            }
        )

        # Creating a toxicity detection enrichment:

        toxicity_enrichment = Enrichment(
            name="content_toxicity",
            columns=["user_comment"],
            enrichment="toxicity_detection",
            config={
                "threshold": 0.7,
                "categories": ["toxic", "severe_toxic", "obscene"]
            }
        )
    """

    # Setting the feature type to ENRICHMENT
    type: Literal['ENRICHMENT'] = CustomFeatureType.ENRICHMENT.value

    # List of input column names used to generate the enrichment
    columns: List[str]

    # String identifier for the enrichment to be applied. e.g. "embedding" or "toxicity"
    enrichment: str

    # Dictionary for additional configuration options for the enrichment
    config: Dict[str, Any] = {}
