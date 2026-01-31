# pylint: disable=too-many-lines
"""Model-related constants for Fiddler AI platform.

This module defines constants used for model configuration, data types, and feature
definitions in Fiddler. These constants enable proper model onboarding, schema
definition, and monitoring setup for various ML and AI model types.

Key Concepts:
    - **Model Input Types**: Define how models consume data (tabular, text, mixed)
    - **Model Tasks**: Specify the ML task type for proper metric calculation
    - **Data Types**: Define column types for schema validation and monitoring
    - **Artifact Status**: Track model artifact upload and surrogate model status
    - **Custom Features**: Enable advanced monitoring for embeddings and multi-column features

Model Onboarding Workflow:
    1. Define model schema with appropriate data types
    2. Specify model task for correct metric calculation
    3. Configure input type for proper data handling
    4. Set up custom features for advanced monitoring
    5. Upload model artifacts for explainability (optional)

Usage Pattern:
    These constants are used throughout the model onboarding process:

    ```python
    import fiddler as fdl

    # Define model specification
    model_spec = fdl.ModelSpec(
        inputs=['feature1', 'feature2'],
        outputs=['prediction'],
        targets=['actual'],
        metadata=['timestamp', 'user_id']
    )

    # Create model with task and input type
    model = fdl.Model.from_data(
        name='my_model',
        project_id=project.id,
        source=training_data,
        spec=model_spec,
        task=fdl.ModelTask.BINARY_CLASSIFICATION,
        input_type=fdl.ModelInputType.TABULAR
    )
    ```

See Also:
    - :class:`~fiddler.entities.Model` for model management and operations
    - :class:`~fiddler.schemas.ModelSpec` for model specification configuration
    - :class:`~fiddler.schemas.ModelSchema` for column schema definitions
    - Fiddler documentation on Models: https://docs.fiddler.ai/technical-reference/api-methods-30#models
"""

from __future__ import annotations

import enum


@enum.unique
class ModelInputType(str, enum.Enum):
    """Input data types supported by Fiddler models.

    This enum defines the different types of input data that models can process.
    The input type determines how Fiddler handles data preprocessing, validation,
    and monitoring for the model.

    Attributes:
        TABULAR: Structured data with rows and columns
        TEXT: Natural language text data
        MIXED: Combination of structured and unstructured data

    Examples:
        Defining model input type during onboarding:

        ```python
        # Tabular data model (traditional ML)
        model = fdl.Model.from_data(
            name='credit_model',
            source=credit_data,
            spec=model_spec,
            task=fdl.ModelTask.BINARY_CLASSIFICATION,
            input_type=fdl.ModelInputType.TABULAR
        )

        # Text-based model (NLP)
        model = fdl.Model.from_data(
            name='sentiment_model',
            source=text_data,
            spec=model_spec,
            task=fdl.ModelTask.MULTICLASS_CLASSIFICATION,
            input_type=fdl.ModelInputType.TEXT
        )

        # Mixed data model (multimodal)
        model = fdl.Model.from_data(
            name='multimodal_model',
            source=mixed_data,
            spec=model_spec,
            task=fdl.ModelTask.REGRESSION,
            input_type=fdl.ModelInputType.MIXED
        )
        ```

    Note:
        Input type affects data validation, preprocessing, and available
        monitoring features. Choose the type that best matches your model's
        primary input data format.
    """

    TABULAR = 'structured'
    """Structured tabular data with rows and columns.

    Used for traditional machine learning models that operate on structured
    datasets with well-defined features. This includes most supervised learning
    models trained on CSV data, database tables, or pandas DataFrames.

    Characteristics:
    - Fixed schema with defined columns
    - Numeric and categorical features
    - Traditional ML algorithms (trees, linear models, etc.)
    - Standard drift detection on individual features

    Typical use cases:
    - Credit scoring models
    - Fraud detection systems
    - Customer churn prediction
    - Sales forecasting models
    - Risk assessment models

    Supported data types: All DataType enum values
    """

    TEXT = 'text'
    """Natural language text data.

    Used for models that primarily process text inputs such as NLP models,
    language models, and text classification systems. Enables text-specific
    monitoring and embedding-based drift detection.

    Characteristics:
    - Text strings as primary input
    - Embedding-based feature monitoring
    - Text-specific preprocessing
    - Language model optimizations

    Typical use cases:
    - Sentiment analysis models
    - Document classification
    - Named entity recognition
    - Text summarization models
    - Chatbots and conversational AI

    Special considerations:
    - May require text embedding custom features
    - Supports text-specific enrichments
    - Drift detection on embedding vectors
    """

    MIXED = 'mixed'
    """Combination of structured and unstructured data.

    Used for multimodal models that process both structured tabular data and
    unstructured data like text, images, or embeddings. Enables comprehensive
    monitoring across different data types.

    Characteristics:
    - Multiple data modalities
    - Complex feature interactions
    - Flexible schema definitions
    - Advanced custom feature support

    Typical use cases:
    - Recommendation systems (user features + content)
    - Fraud detection (transaction data + text descriptions)
    - Medical diagnosis (structured data + images/text)
    - E-commerce search (product features + text queries)
    - Content moderation (metadata + text/images)

    Special considerations:
    - Requires careful schema design
    - May need multiple custom feature types
    - Complex drift monitoring setup
    """


@enum.unique
class ModelTask(str, enum.Enum):
    """Machine learning task types supported by Fiddler.

    This enum defines the different types of ML tasks that Fiddler can monitor.
    The task type determines which metrics are calculated, how performance is
    measured, and what monitoring capabilities are available.

    Task-Specific Features:
        - **Classification**: Accuracy, precision, recall, F1, AUC, confusion matrix
        - **Regression**: MAE, MSE, RMSE, R², residual analysis
        - **Ranking**: NDCG, MAP, precision@k, ranking-specific metrics
        - **LLM**: Token-based metrics, response quality, safety metrics

    Attributes:
        BINARY_CLASSIFICATION: Two-class classification problems
        MULTICLASS_CLASSIFICATION: Multi-class classification problems
        REGRESSION: Continuous value prediction problems
        RANKING: Ranking and recommendation problems
        LLM: Large language model and generative AI tasks
        NOT_SET: Placeholder for undefined tasks

    Examples:
        Configuring models for different tasks:

        ```python
        # Binary classification (fraud detection)
        fraud_model = fdl.Model.from_data(
            name='fraud_detector',
            source=fraud_data,
            spec=model_spec,
            task=fdl.ModelTask.BINARY_CLASSIFICATION,
            task_params=fdl.ModelTaskParams(
                binary_classification_threshold=0.5
            )
        )

        # Multiclass classification (sentiment analysis)
        sentiment_model = fdl.Model.from_data(
            name='sentiment_analyzer',
            source=sentiment_data,
            spec=model_spec,
            task=fdl.ModelTask.MULTICLASS_CLASSIFICATION,
            task_params=fdl.ModelTaskParams(
                target_class_order=['negative', 'neutral', 'positive']
            )
        )

        # Regression (price prediction)
        price_model = fdl.Model.from_data(
            name='price_predictor',
            source=price_data,
            spec=model_spec,
            task=fdl.ModelTask.REGRESSION
        )

        # Ranking (recommendation system)
        ranking_model = fdl.Model.from_data(
            name='recommender',
            source=ranking_data,
            spec=model_spec,
            task=fdl.ModelTask.RANKING,
            task_params=fdl.ModelTaskParams(
                group_by='user_id',
                top_k=10
            )
        )

        # LLM (language model)
        llm_model = fdl.Model.from_data(
            name='chatbot',
            source=conversation_data,
            spec=model_spec,
            task=fdl.ModelTask.LLM
        )
        ```

    Note:
        Task type cannot be changed after model creation. Choose carefully
        based on your model's primary objective and output format.
    """

    BINARY_CLASSIFICATION = 'binary_classification'
    """Two-class classification tasks.

    Used for models that predict one of two possible outcomes or classes.
    Enables binary classification metrics and threshold-based analysis.

    Available metrics:
    - Accuracy, Precision, Recall, F1-score
    - AUC-ROC, AUC-PR curves
    - Confusion matrix analysis
    - Threshold optimization tools

    Typical use cases:
    - Fraud detection (fraud/legitimate)
    - Email spam filtering (spam/ham)
    - Medical diagnosis (positive/negative)
    - Credit approval (approve/deny)
    - Churn prediction (churn/retain)

    Required outputs: Single probability score or binary prediction
    Task parameters: binary_classification_threshold
    """

    MULTICLASS_CLASSIFICATION = 'multiclass_classification'
    """Multi-class classification tasks.

    Used for models that predict one of multiple possible classes or categories.
    Supports comprehensive multiclass performance analysis and class-specific metrics.

    Available metrics:
    - Per-class precision, recall, F1-score
    - Macro and micro-averaged metrics
    - Confusion matrix with multiple classes
    - Class distribution analysis

    Typical use cases:
    - Document categorization (multiple topics)
    - Image classification (multiple objects)
    - Sentiment analysis (positive/neutral/negative)
    - Product categorization
    - Intent classification in chatbots

    Required outputs: Class probabilities or single class prediction
    Task parameters: target_class_order, class_weights
    """

    REGRESSION = 'regression'
    """Continuous value prediction tasks.

    Used for models that predict numerical values on a continuous scale.
    Enables regression-specific metrics and residual analysis.

    Available metrics:
    - Mean Absolute Error (MAE)
    - Mean Squared Error (MSE)
    - Root Mean Squared Error (RMSE)
    - R-squared (coefficient of determination)
    - Residual distribution analysis

    Typical use cases:
    - Price prediction
    - Sales forecasting
    - Risk scoring (continuous scores)
    - Demand forecasting
    - Performance rating prediction

    Required outputs: Single continuous numerical value
    Task parameters: None (uses standard regression metrics)
    """

    RANKING = 'ranking'
    """Ranking and recommendation tasks.

    Used for models that rank items or provide ordered recommendations.
    Supports ranking-specific metrics and list-wise evaluation.

    Available metrics:
    - Normalized Discounted Cumulative Gain (NDCG)
    - Mean Average Precision (MAP)
    - Precision@K, Recall@K
    - Mean Reciprocal Rank (MRR)
    - Hit Rate analysis

    Typical use cases:
    - Search result ranking
    - Product recommendations
    - Content recommendation systems
    - Information retrieval
    - Personalized ranking

    Required outputs: Ranked list of items with scores
    Task parameters: group_by (session/user ID), top_k
    Special data format: Grouped by query/session identifier
    """

    LLM = 'llm'
    """Large language model and generative AI tasks.

    Used for language models, chatbots, and generative AI applications.
    Enables LLM-specific monitoring including safety, quality, and performance metrics.

    Available metrics:
    - Response quality metrics
    - Safety and toxicity detection
    - Hallucination detection
    - Token-based analysis
    - Latency and throughput metrics

    Typical use cases:
    - Chatbots and conversational AI
    - Text generation models
    - Question-answering systems
    - Code generation models
    - Content creation assistants

    Special features:
    - Guardrails integration
    - Safety monitoring
    - Prompt and response analysis
    - Token usage tracking
    """

    NOT_SET = 'not_set'
    """Placeholder for undefined or unspecified tasks.

    Used as a default value when the model task has not been explicitly
    defined. Should be replaced with an appropriate task type during
    model configuration.

    This value should not be used for production models as it limits
    available monitoring capabilities and metrics.
    """

    def is_classification(self) -> bool:
        """Check if the task is a classification type.

        Returns:
            bool: True if task is binary or multiclass classification
        """
        return self in {
            ModelTask.BINARY_CLASSIFICATION,
            ModelTask.MULTICLASS_CLASSIFICATION,
        }

    def is_regression(self) -> bool:
        """Check if the task is regression.

        Returns:
            bool: True if task is regression
        """
        return self == ModelTask.REGRESSION


@enum.unique
class DataType(str, enum.Enum):
    """Data types supported for model columns in Fiddler.

    This enum defines the supported data types for model schema columns.
    Data types determine how Fiddler processes, validates, and monitors
    individual columns in your model's input and output data.

    Type Categories:
        - **Numeric**: FLOAT, INTEGER - enable statistical analysis
        - **Categorical**: BOOLEAN, CATEGORY - enable distribution analysis
        - **Textual**: STRING - enable text-based monitoring
        - **Temporal**: TIMESTAMP - enable time-based analysis
        - **Vector**: VECTOR - enable embedding-based monitoring

    Attributes:
        FLOAT: Floating-point numerical values
        INTEGER: Integer numerical values
        BOOLEAN: True/false binary values
        STRING: Text string values
        CATEGORY: Categorical values with limited distinct options
        TIMESTAMP: Date/time values
        VECTOR: Multi-dimensional numerical vectors (embeddings)

    Examples:
        Defining column data types in model schema:

        ```python
        from fiddler import Column, DataType

        # Define columns with appropriate data types
        columns = [
            Column(name='age', data_type=DataType.INTEGER),
            Column(name='income', data_type=DataType.FLOAT),
            Column(name='is_member', data_type=DataType.BOOLEAN),
            Column(name='category', data_type=DataType.CATEGORY),
            Column(name='description', data_type=DataType.STRING),
            Column(name='created_at', data_type=DataType.TIMESTAMP),
            Column(name='embedding', data_type=DataType.VECTOR)
        ]

        # Create model schema
        schema = fdl.ModelSchema(columns=columns)
        ```

        Data type validation and monitoring:

        ```python
        # Numeric types enable statistical monitoring
        if column.data_type.is_numeric():
            # Statistical drift detection available
            # Range validation enabled
            # Distribution analysis supported
            pass

        # Categorical types enable distribution monitoring
        if column.data_type.is_bool_or_cat():
            # Category distribution tracking
            # New category detection
            # Frequency analysis
            pass

        # Vector types enable embedding monitoring
        if column.data_type.is_vector():
            # Embedding drift detection
            # Clustering analysis
            # Dimensionality monitoring
            pass
        ```

    Note:
        Choose data types that accurately represent your data for optimal
        monitoring and validation. Incorrect data types may lead to
        inappropriate metrics or monitoring failures.
    """

    FLOAT = 'float'
    """Floating-point numerical values.

    Used for continuous numerical data with decimal precision. Enables
    comprehensive statistical analysis and numerical drift detection.

    Characteristics:
    - Decimal precision values
    - Statistical distribution analysis
    - Range and outlier detection
    - Correlation analysis support

    Monitoring features:
    - Mean, median, standard deviation tracking
    - Distribution drift detection (KS test, PSI)
    - Range violation alerts
    - Outlier detection and analysis

    Typical use cases:
    - Prices, costs, revenues
    - Probabilities and confidence scores
    - Measurements and sensor readings
    - Performance metrics and ratios
    - Model prediction scores

    Validation: Numeric range checks, NaN detection
    """

    INTEGER = 'int'
    """Integer numerical values.

    Used for whole number data without decimal places. Supports numerical
    analysis while recognizing discrete nature of integer data.

    Characteristics:
    - Whole number values only
    - Discrete distribution analysis
    - Count-based statistics
    - Range validation

    Monitoring features:
    - Count distribution tracking
    - Range violation detection
    - Discrete value frequency analysis
    - Statistical drift detection

    Typical use cases:
    - Counts and quantities
    - Age, years, days
    - IDs and identifiers (when numeric)
    - Ranking positions
    - Categorical codes (when numeric)

    Validation: Integer format checks, range validation
    """

    BOOLEAN = 'bool'
    """True/false binary values.

    Used for binary flag data with exactly two possible values. Enables
    binary distribution analysis and proportion tracking.

    Characteristics:
    - Exactly two values (True/False, 1/0, Yes/No)
    - Binary distribution analysis
    - Proportion-based metrics
    - Simple categorical handling

    Monitoring features:
    - True/False ratio tracking
    - Binary distribution drift
    - Proportion change detection
    - Flag frequency analysis

    Typical use cases:
    - Feature flags and indicators
    - Binary classifications
    - Yes/No survey responses
    - Membership status
    - Activation states

    Validation: Binary value format checks
    """

    STRING = 'str'
    """Text string values.

    Used for textual data of variable length. Supports text-based analysis
    and can be combined with text embeddings for advanced monitoring.

    Characteristics:
    - Variable length text
    - Text-based analysis
    - String pattern detection
    - Encoding-aware processing

    Monitoring features:
    - Length distribution tracking
    - Pattern and format analysis
    - Text embedding integration
    - String uniqueness analysis

    Typical use cases:
    - Names and descriptions
    - Comments and reviews
    - URLs and paths
    - Free-form text inputs
    - JSON or XML strings

    Special considerations:
    - Can be converted to embeddings for semantic monitoring
    - Supports text enrichment features
    - May require text preprocessing
    """

    CATEGORY = 'category'
    """Categorical values with limited distinct options.

    Used for data with a finite set of possible values or categories.
    Enables categorical distribution analysis and new category detection.

    Characteristics:
    - Limited set of possible values
    - Categorical distribution tracking
    - Category frequency analysis
    - New category detection

    Monitoring features:
    - Category distribution drift
    - New/missing category alerts
    - Frequency change detection
    - Category proportion analysis

    Typical use cases:
    - Product categories
    - Geographic regions
    - Status codes
    - Demographic categories
    - Classification labels

    Best practices:
    - Use for data with < 1000 unique values
    - Consider STRING type for high-cardinality categories
    - Define expected categories during schema creation
    """

    TIMESTAMP = 'timestamp'
    """Date and time values.

    Used for temporal data including dates, times, and timestamps.
    Enables time-based analysis and temporal pattern detection.

    Characteristics:
    - Date/time information
    - Temporal ordering
    - Time-based aggregations
    - Timezone awareness

    Monitoring features:
    - Temporal pattern analysis
    - Time gap detection
    - Seasonal trend monitoring
    - Data freshness tracking

    Typical use cases:
    - Event timestamps
    - Creation/modification dates
    - Transaction times
    - Log timestamps
    - Scheduled events

    Supported formats:
    - Unix timestamps
    - ISO 8601 strings
    - Pandas datetime objects
    - Various date formats (with parsing)
    """

    VECTOR = 'vector'
    """Multi-dimensional numerical vectors (embeddings).

    Used for embedding vectors, feature vectors, and other multi-dimensional
    numerical data. Enables embedding-based drift detection and clustering analysis.

    Characteristics:
    - Fixed-dimension numerical arrays
    - Embedding-based analysis
    - Vector similarity metrics
    - Clustering support

    Monitoring features:
    - Embedding drift detection
    - Cluster analysis and visualization
    - Vector similarity tracking
    - Dimensionality validation

    Typical use cases:
    - Text embeddings (Word2Vec, BERT, etc.)
    - Image embeddings (CNN features)
    - User/item embeddings
    - Feature vectors from neural networks
    - Recommendation system embeddings

    Special considerations:
    - Requires consistent vector dimensions
    - Benefits from custom feature definitions
    - Supports clustering and UMAP visualization
    """

    def is_numeric(self) -> bool:
        """Check if the data type is numeric.

        Returns:
            bool: True if data type is INTEGER or FLOAT
        """
        return self in {DataType.INTEGER, DataType.FLOAT}

    def is_bool_or_cat(self) -> bool:
        """Check if the data type is boolean or categorical.

        Returns:
            bool: True if data type is BOOLEAN or CATEGORY
        """
        return self in {DataType.BOOLEAN, DataType.CATEGORY}

    def is_vector(self) -> bool:
        """Check if the data type is vector.

        Returns:
            bool: True if data type is VECTOR
        """
        return self == DataType.VECTOR


@enum.unique
class ArtifactStatus(str, enum.Enum):
    """Model artifact upload and deployment status.

    This enum tracks the status of model artifacts in Fiddler, indicating
    whether explainability features are available and what type of model
    deployment is active.

    Artifact Types:
        - **No Model**: No artifacts uploaded, monitoring only
        - **Surrogate**: Fiddler-generated surrogate model for explainability
        - **User Uploaded**: User-provided model artifacts for full explainability

    Attributes:
        NO_MODEL: No model artifacts available
        SURROGATE: Surrogate model generated by Fiddler
        USER_UPLOADED: User-provided model artifacts uploaded

    Examples:
        Checking artifact status and capabilities:

        ```python
        # Check current artifact status
        model = fdl.Model.from_name('my_model', project_id=project.id)

        if model.artifact_status == fdl.ArtifactStatus.NO_MODEL:
            print("Monitoring only - no explainability features")
        elif model.artifact_status == fdl.ArtifactStatus.SURROGATE:
            print("Surrogate model available - basic explainability")
        elif model.artifact_status == fdl.ArtifactStatus.USER_UPLOADED:
            print("Full model artifacts - complete explainability")

        # Upload model artifacts to enable explainability
        if model.artifact_status == fdl.ArtifactStatus.NO_MODEL:
            job = model.add_artifact(
                model_dir='./model_package/',
                deployment_params=fdl.DeploymentParams(
                    artifact_type=fdl.ArtifactType.PYTHON_PACKAGE
                )
            )
            job.wait()
        ```

    Note:
        Artifact status affects available explainability features. User-uploaded
        artifacts provide the most comprehensive explanation capabilities.
    """

    NO_MODEL = 'no_model'
    """No model artifacts have been uploaded.

    The model exists in Fiddler for monitoring purposes only. Data drift
    detection, performance monitoring, and alerting are available, but
    explainability features are not accessible.

    Available features:
    - Data drift monitoring
    - Performance metric tracking
    - Alert rule configuration
    - Dashboard visualization
    - Data publishing and monitoring

    Unavailable features:
    - Point explainability
    - Global feature importance
    - Model artifact-based analysis
    - Custom explanation methods

    This is the default status for newly created models before any
    artifacts are uploaded.
    """

    SURROGATE = 'surrogate'
    """Surrogate model generated by Fiddler for explainability.

    Fiddler has automatically generated a surrogate model based on your
    published data to provide basic explainability features. The surrogate
    model approximates your original model's behavior.

    Available features:
    - Basic point explainability
    - Global feature importance
    - Approximated explanations
    - All monitoring features

    Characteristics:
    - Automatically generated by Fiddler
    - Approximates original model behavior
    - Provides reasonable explanation quality
    - No additional setup required

    Limitations:
    - May not perfectly match original model
    - Limited to surrogate model capabilities
    - Cannot use custom explanation methods
    """

    USER_UPLOADED = 'user_uploaded'
    """User-provided model artifacts have been uploaded.

    Complete model artifacts have been uploaded, enabling full explainability
    features with the actual model. This provides the highest quality
    explanations and complete feature access.

    Available features:
    - Full point explainability with actual model
    - Global feature importance from actual model
    - Custom explanation methods (if defined)
    - Model artifact-based analysis
    - All monitoring and surrogate features

    Characteristics:
    - Uses actual uploaded model
    - Highest explanation accuracy
    - Supports custom explanation methods
    - Complete feature access

    Requirements:
    - Model artifacts must be properly packaged
    - Compatible with Fiddler's deployment environment
    - May require specific Python dependencies
    """


@enum.unique
class CustomFeatureType(str, enum.Enum):
    """Types of custom features for advanced model monitoring.

    This enum defines different types of custom features that can be created
    for advanced monitoring scenarios. Custom features enable monitoring of
    complex data types, embeddings, and multi-column relationships.

    Feature Categories:
        - **Multi-column**: Features derived from multiple input columns
        - **Vector-based**: Features from embedding or vector columns
        - **Embedding-specific**: Specialized embedding monitoring
        - **Enrichment**: Features from data enrichment processes

    Attributes:
        FROM_COLUMNS: Multi-column derived features
        FROM_VECTOR: Single vector column features
        FROM_TEXT_EMBEDDING: Text embedding features
        FROM_IMAGE_EMBEDDING: Image embedding features
        ENRICHMENT: Enrichment-derived features

    Examples:
        Creating different types of custom features:

        ```python
        # Multi-column feature for monitoring column interactions
        multivariate_feature = fdl.Multivariate(
            name='user_profile',
            columns=['age', 'income', 'location'],
            monitor_components=True
        )

        # Vector feature for embedding monitoring
        vector_feature = fdl.VectorFeature(
            name='product_embedding',
            column='product_vector',
            n_clusters=10
        )

        # Text embedding feature with clustering
        text_embedding = fdl.TextEmbedding(
            name='review_sentiment',
            column='review_embedding',
            n_clusters=5,
            n_tags=10
        )

        # Image embedding feature
        image_embedding = fdl.ImageEmbedding(
            name='image_features',
            column='image_embedding',
            n_clusters=8
        )

        # Enrichment feature for data validation
        enrichment_feature = fdl.Enrichment(
            name='email_validation',
            enrichment='email_validation',
            columns=['email_address'],
            config={'strict': True}
        )
        ```

    Note:
        Custom features enable advanced monitoring capabilities but require
        careful configuration to match your specific use case and data structure.
    """

    FROM_COLUMNS = 'FROM_COLUMNS'
    """Multi-column derived features (Multivariate).

    Used for creating custom features that monitor relationships and
    interactions between multiple input columns. Enables detection of
    drift patterns across column combinations.

    Characteristics:
    - Monitors multiple columns as a single feature
    - Detects multi-dimensional drift patterns
    - Can monitor individual components separately
    - Supports complex feature interactions

    Use cases:
    - Geographic coordinates (latitude, longitude)
    - User profiles (age, income, location)
    - Product specifications (dimensions, weight, price)
    - Time series components (trend, seasonality)

    Configuration:
    - Specify list of columns to monitor together
    - Optional component monitoring
    - Clustering for dimensionality reduction
    """

    FROM_VECTOR = 'FROM_VECTOR'
    """Single vector column features (VectorFeature).

    Used for monitoring embedding vectors or other high-dimensional
    numerical arrays as single features. Enables clustering-based
    drift detection and embedding analysis.

    Characteristics:
    - Monitors single vector/embedding column
    - Clustering-based drift detection
    - Dimensionality reduction visualization
    - Vector similarity analysis

    Use cases:
    - Word embeddings (Word2Vec, GloVe)
    - Neural network hidden layer outputs
    - Feature vectors from autoencoders
    - Learned representations

    Configuration:
    - Specify vector column name
    - Set number of clusters for monitoring
    - Optional source column reference
    """

    FROM_TEXT_EMBEDDING = 'FROM_TEXT_EMBEDDING'
    """Text embedding features (TextEmbedding).

    Specialized for monitoring text embeddings with text-specific
    analysis capabilities. Includes TF-IDF summarization and
    text-aware clustering.

    Characteristics:
    - Text-specific embedding analysis
    - TF-IDF token summarization
    - Text-aware clustering
    - Semantic drift detection

    Use cases:
    - BERT, GPT embeddings
    - Document embeddings
    - Sentence transformers
    - Text classification features

    Configuration:
    - Specify embedding column
    - Set number of clusters
    - Configure TF-IDF tags per cluster
    """

    FROM_IMAGE_EMBEDDING = 'FROM_IMAGE_EMBEDDING'
    """Image embedding features (ImageEmbedding).

    Specialized for monitoring image embeddings and visual features
    extracted from images. Optimized for computer vision model
    monitoring.

    Characteristics:
    - Image-specific embedding analysis
    - Visual feature clustering
    - Image-aware drift detection
    - Computer vision optimizations

    Use cases:
    - CNN feature extractions
    - Image classification embeddings
    - Object detection features
    - Visual similarity vectors

    Configuration:
    - Specify embedding column
    - Set clustering parameters
    - Image-specific preprocessing
    """

    ENRICHMENT = 'ENRICHMENT'
    """Enrichment-derived features (Enrichment).

    Used for features created through data enrichment processes
    such as validation, transformation, or external data augmentation.
    Enables monitoring of enriched data quality and consistency.

    Characteristics:
    - Derived from enrichment processes
    - Data quality monitoring
    - Validation result tracking
    - Transformation monitoring

    Use cases:
    - Email validation results
    - Address standardization
    - Data quality scores
    - External API enrichments

    Configuration:
    - Specify enrichment type
    - Configure enrichment parameters
    - Set input columns for enrichment
    """
