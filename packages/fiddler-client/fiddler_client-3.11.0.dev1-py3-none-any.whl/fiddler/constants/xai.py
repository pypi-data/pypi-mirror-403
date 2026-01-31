"""Explainability (XAI) constants for Fiddler AI platform.

This module defines constants for explainability features in Fiddler, including
explanation methods for model interpretability and file formats for downloading
explanation data. These constants enable configuration of explainability analysis
and interpretation of model predictions.

Key Concepts:
    - **Explanation Methods**: Different algorithms for computing feature importance
    - **Download Formats**: File formats for exporting explanation results
    - **Model Interpretability**: Understanding how models make predictions

Usage Pattern:
    XAI constants are used when configuring explainability analysis:

    ```python
    import fiddler as fdl

    # Configure explanation parameters
    xai_params = fdl.XaiParams(
        custom_explain_methods=['custom_method'],
        default_explain_method=fdl.ExplainMethod.SHAP
    )

    # Generate explanations
    explanations = model.explain(
        data_source=fdl.RowDataSource(row=sample_data),
        explain_method=fdl.ExplainMethod.FIDDLER_SHAP
    )

    # Download explanation results
    explanation_data = model.download_explanations(
        format=fdl.DownloadFormat.PARQUET,
        chunk_size=1000
    )
    ```

See Also:
    - :class:`~fiddler.schemas.XaiParams` for explainability parameter configuration
    - :class:`~fiddler.schemas.xai` for data source configurations
    - Fiddler documentation on Explainability: https://docs.fiddler.ai/technical-reference/api-methods-30#explainability
"""

import enum


@enum.unique
class ExplainMethod(str, enum.Enum):
    """Explanation methods for model interpretability and feature importance analysis.

    This enum defines the available algorithms for computing feature importance
    and generating explanations for model predictions. Different methods provide
    different perspectives on how features contribute to model decisions.

    Method Categories:
        - **SHAP-based**: Unified framework for feature importance (SHAP, FIDDLER_SHAP)
        - **Gradient-based**: Uses model gradients for explanations (IG)
        - **Perturbation-based**: Feature permutation and baseline methods

    Attributes:
        SHAP: Standard SHAP (SHapley Additive exPlanations) implementation
        FIDDLER_SHAP: Fiddler's optimized SHAP implementation for better performance
        IG: Integrated Gradients method using model gradients
        PERMUTE: Permutation-based feature importance analysis
        ZERO_RESET: Zero baseline reset method for feature ablation
        MEAN_RESET: Mean baseline reset method for feature ablation

    Examples:
        Using different explanation methods:

        ```python
        # Standard SHAP explanations
        shap_explanations = model.explain(
            data_source=fdl.RowDataSource(row=sample_data),
            explain_method=fdl.ExplainMethod.SHAP
        )

        # Fiddler's optimized SHAP (recommended)
        fast_explanations = model.explain(
            data_source=fdl.RowDataSource(row=sample_data),
            explain_method=fdl.ExplainMethod.FIDDLER_SHAP
        )

        # Integrated Gradients for neural networks
        ig_explanations = model.explain(
            data_source=fdl.RowDataSource(row=sample_data),
            explain_method=fdl.ExplainMethod.IG
        )

        # Permutation importance
        perm_explanations = model.explain(
            data_source=fdl.RowDataSource(row=sample_data),
            explain_method=fdl.ExplainMethod.PERMUTE
        )
        ```

    Note:
        Method availability depends on model type and artifact configuration.
        FIDDLER_SHAP is recommended for most use cases due to performance optimizations.
    """

    SHAP = 'SHAP'
    """Standard SHAP (SHapley Additive exPlanations) method.

    Implements the original SHAP algorithm for computing feature importance
    based on game theory. Provides globally consistent and locally accurate
    feature attributions that sum to the difference between model output
    and expected output.

    Characteristics:
    - Theoretically grounded in game theory
    - Satisfies efficiency, symmetry, dummy, and additivity axioms
    - Works with any machine learning model
    - Computationally intensive for complex models

    Best for:
    - Research and academic applications
    - When theoretical guarantees are important
    - Comparative analysis with other SHAP implementations
    """

    FIDDLER_SHAP = 'FIDDLER_SHAP'
    """Fiddler's optimized SHAP implementation for improved performance.

    Fiddler's enhanced version of SHAP that provides the same theoretical
    guarantees as standard SHAP but with significant performance improvements
    and optimizations for production use cases.

    Characteristics:
    - Same theoretical properties as standard SHAP
    - Significant performance optimizations
    - Better suited for production environments
    - Optimized for Fiddler's infrastructure

    Best for:
    - Production explainability workflows
    - High-volume explanation generation
    - Real-time explanation requirements
    - Most general-purpose use cases (recommended)
    """

    IG = 'IG'
    """Integrated Gradients method for gradient-based explanations.

    Computes feature importance by integrating gradients of the model output
    with respect to inputs along a straight path from a baseline to the input.
    Particularly effective for neural networks and differentiable models.

    Characteristics:
    - Uses model gradients for attribution
    - Satisfies implementation invariance and sensitivity axioms
    - Requires differentiable models
    - Effective for neural networks

    Best for:
    - Neural network models
    - Deep learning applications
    - When gradient information is available
    - Image and text models with embeddings
    """

    PERMUTE = 'PERMUTE'
    """Permutation-based feature importance analysis.

    Computes feature importance by measuring the decrease in model performance
    when feature values are randomly permuted. Provides model-agnostic
    importance scores based on predictive contribution.

    Characteristics:
    - Model-agnostic approach
    - Based on predictive performance impact
    - Computationally straightforward
    - Provides global feature importance

    Best for:
    - Model-agnostic analysis
    - Understanding overall feature importance
    - Comparing feature relevance across models
    - When other methods are not applicable
    """

    ZERO_RESET = 'ZERO_RESET'
    """Zero baseline reset method for feature ablation analysis.

    Computes feature importance by replacing feature values with zero and
    measuring the change in model output. Provides insights into how
    features contribute relative to a zero baseline.

    Characteristics:
    - Simple ablation-based approach
    - Uses zero as the baseline value
    - Fast computation
    - May not be suitable for all feature types

    Best for:
    - Quick feature importance analysis
    - Models where zero is a meaningful baseline
    - Sparse feature representations
    - Initial feature importance exploration
    """

    MEAN_RESET = 'MEAN_RESET'
    """Mean baseline reset method for feature ablation analysis.

    Computes feature importance by replacing feature values with their
    population mean and measuring the change in model output. Uses the
    training data mean as a more representative baseline than zero.

    Characteristics:
    - Ablation-based with mean baseline
    - Uses training data statistics
    - More representative baseline than zero
    - Accounts for feature distributions

    Best for:
    - Models where mean is a natural baseline
    - Features with non-zero typical values
    - When training distribution is representative
    - Comparative analysis with zero baseline
    """


@enum.unique
class DownloadFormat(str, enum.Enum):
    """File formats for downloading and exporting explanation data.

    This enum defines the supported file formats for downloading explanation
    results from Fiddler. Different formats offer different advantages in
    terms of performance, compatibility, and data structure preservation.

    Attributes:
        PARQUET: Apache Parquet format for efficient columnar storage
        CSV: Comma-separated values format for broad compatibility

    Examples:
        Downloading explanations in different formats:

        ```python
        # Download as Parquet (recommended for large datasets)
        parquet_data = model.download_explanations(
            format=fdl.DownloadFormat.PARQUET,
            chunk_size=1000
        )

        # Download as CSV (better compatibility)
        csv_data = model.download_explanations(
            format=fdl.DownloadFormat.CSV,
            chunk_size=500
        )
        ```

    Note:
        Choose format based on your analysis tools and data size requirements.
        Parquet is recommended for large datasets due to compression and performance.
    """

    PARQUET = 'PARQUET'
    """Apache Parquet format for efficient columnar data storage.

    Parquet is a columnar storage format that provides excellent compression
    and query performance. It preserves data types and schema information,
    making it ideal for analytical workloads and large datasets.

    Advantages:
    - Excellent compression ratios
    - Fast query performance
    - Preserves data types and schema
    - Efficient for analytical operations

    Best for:
    - Large explanation datasets
    - Analytical workflows
    - Integration with data science tools
    - Long-term data storage
    """

    CSV = 'CSV'
    """Comma-separated values format for broad tool compatibility.

    CSV is a simple, widely-supported text format that can be opened by
    virtually any data analysis tool, spreadsheet application, or programming
    language. While less efficient than Parquet, it offers maximum compatibility.

    Advantages:
    - Universal compatibility
    - Human-readable format
    - Simple structure
    - Supported by all tools

    Best for:
    - Small to medium datasets
    - Sharing with non-technical users
    - Quick data inspection
    - Integration with legacy systems
    """


DEFAULT_DOWNLOAD_CHUNK_SIZE = 1000
"""Default chunk size for downloading explanation data in batches.

This constant defines the default number of explanation records to download
in each batch when retrieving explanation data from Fiddler. Chunking helps
manage memory usage and provides progress feedback for large datasets.

Characteristics:
- Balances memory usage and download efficiency
- Provides reasonable progress granularity
- Can be overridden based on specific needs
- Suitable for most use cases

Usage:
    chunk_size parameter in download methods defaults to this value if not specified.
    Adjust based on available memory and network performance requirements.
"""
