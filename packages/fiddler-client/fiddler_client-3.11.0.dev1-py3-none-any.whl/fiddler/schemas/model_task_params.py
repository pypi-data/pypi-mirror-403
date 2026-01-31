from typing import List, Optional

from fiddler.schemas.base import BaseModel


class ModelTaskParams(BaseModel):
    """Configuration parameters for different model task types and evaluation metrics.

    ModelTaskParams defines task-specific parameters that control how models are
    evaluated and monitored within Fiddler. Different model types (classification,
    regression, ranking) require different parameters to properly compute metrics
    and perform analysis.

    These parameters are essential for accurate metric computation, proper baseline
    establishment, and meaningful performance monitoring across different model
    types and use cases.

    Attributes:
        binary_classification_threshold: Decision threshold for binary classification models
        target_class_order: Ordered list of target classes for multi-class models
        group_by: Column name used for grouping in ranking models (query/session ID)
        top_k: Number of top results to consider for ranking metric computation
        class_weights: Weight assigned to each class for weighted metrics
        weighted_ref_histograms: Whether to use weighted histograms for drift detection

    Examples:
        Configuration for binary classification:

        binary_params = ModelTaskParams(
            binary_classification_threshold=0.5,
            target_class_order=["negative", "positive"]
        )

        Configuration for multi-class classification with class weights:

        multiclass_params = ModelTaskParams(
            target_class_order=["class_a", "class_b", "class_c"],
            class_weights=[0.3, 0.5, 0.2],
            weighted_ref_histograms=True
        )

        Configuration for ranking models:

        ranking_params = ModelTaskParams(
            group_by="query_id",
            top_k=10,
            target_class_order=["not_relevant", "relevant", "highly_relevant"]
        )

        Configuration for imbalanced datasets:

        imbalanced_params = ModelTaskParams(
            binary_classification_threshold=0.3,
            class_weights=[0.1, 0.9],
            weighted_ref_histograms=True
        )
    """
    binary_classification_threshold: Optional[float] = None
    """Threshold for labels"""

    target_class_order: Optional[List] = None
    """Order of target classes"""

    group_by: Optional[str] = None
    """Query/session id column for ranking models"""

    top_k: Optional[int] = None
    """Top k results to consider when computing ranking metrics"""

    class_weights: Optional[List[float]] = None
    """Weight of each classes"""

    weighted_ref_histograms: Optional[bool] = None
    """Whether baseline histograms must be weighted or not while drift metrics"""
