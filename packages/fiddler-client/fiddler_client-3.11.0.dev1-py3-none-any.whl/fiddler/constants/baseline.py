"""
Baseline constants for the Fiddler Python client.

This module defines constants related to baseline configurations in the Fiddler platform.
Baselines serve as reference points for data drift detection by establishing expected
data distributions for model inputs and outputs. They represent the ideal data that
your model works best on and enable Fiddler to detect when production data deviates
from expected patterns.

Key Concepts:
    - **Baseline Types**: Static vs. rolling baseline computation strategies
    - **Window Bin Sizes**: Time granularities for rolling baseline data aggregation
    - **Drift Detection**: Statistical comparison between production data and baselines
    - **Representative Sampling**: Baselines should contain enough data for proper distribution coverage

Baseline Types in Fiddler:
    1. **Static Pre-production**: Created from training/testing datasets via model.publish()
    2. **Static Production**: Defined using specific time ranges of production data
    3. **Rolling Production**: Dynamic sliding window that shifts with time
    4. **Default Static**: Automatically created baseline spanning 15 months around model creation

Baseline Design Guidelines:
    - Include enough data for representative sample of expected distributions
    - Consider including extreme values (min/max) for range violation monitoring
    - Training data is typically the best choice for baseline datasets
    - Ensure coverage of all distinct categorical values expected in production

Example:
    # Static pre-production baseline from training data
    baseline_job = model.publish(
        source=training_data_df,
        environment=fdl.EnvType.PRE_PRODUCTION,
        dataset_name="training_baseline"
    )

    # Static production baseline using time range
    static_baseline = fdl.Baseline(
        name="static_prod_baseline",
        model_id=model.id,
        environment=fdl.EnvType.PRODUCTION,
        type_=fdl.BaselineType.STATIC,
        start_time=(datetime.now() - timedelta(days=7)).timestamp(),
        end_time=(datetime.now() - timedelta(days=1)).timestamp()
    ).create()

    # Rolling production baseline with weekly window
    rolling_baseline = fdl.Baseline(
        name="rolling_baseline",
        model_id=model.id,
        environment=fdl.EnvType.PRODUCTION,
        type_=fdl.BaselineType.ROLLING,
        window_bin_size=fdl.WindowBinSize.WEEK,
        offset_delta=4  # 4 weeks offset
    ).create()

Note:
    Baselines are essential for data drift detection. Choose baseline types based on
    your monitoring needs: static for consistent reference points, rolling for
    adaptive monitoring of time-sensitive patterns.
"""
import enum


@enum.unique
class BaselineType(str, enum.Enum):
    """
    Baseline computation strategies for data drift detection in Fiddler.

    Baseline types determine how reference data is defined and used for comparison
    with production model behavior. Fiddler supports static and rolling baselines,
    each serving different monitoring needs and use cases.

    Static Baselines:
        - Fixed reference point that doesn't change over time
        - Can be created from pre-production data (training/test sets) or production data
        - Consistent comparison point for detecting absolute drift
        - Ideal for compliance, audit requirements, and stable model environments
        - Pre-production static baselines created via model.publish() with PRE_PRODUCTION environment
        - Production static baselines defined using specific time ranges

    Rolling Baselines:
        - Dynamic sliding window that shifts with time
        - Always maintains fixed time distance from current data (e.g., 4 weeks ago)
        - Automatically adapts to gradual changes in data patterns
        - Excellent for detecting sudden changes or anomalies in time-sensitive data
        - Requires window_bin_size and offset_delta parameters

    Selection Guidelines:
        - Use STATIC for regulatory compliance, model validation, and stable environments
        - Use ROLLING for seasonal patterns, evolving data, and operational monitoring
        - Static pre-production baselines are recommended for most use cases
        - Rolling baselines work best with sufficient historical production data

    Example:
        # Static production baseline using time range
        static_baseline = fdl.Baseline(
            name="static_baseline",
            model_id=model.id,
            environment=fdl.EnvType.PRODUCTION,
            type_=fdl.BaselineType.STATIC,
            start_time=(datetime.now() - timedelta(days=30)).timestamp(),
            end_time=(datetime.now() - timedelta(days=7)).timestamp()
        ).create()

        # Rolling production baseline with monthly window
        rolling_baseline = fdl.Baseline(
            name="rolling_baseline",
            model_id=model.id,
            environment=fdl.EnvType.PRODUCTION,
            type_=fdl.BaselineType.ROLLING,
            window_bin_size=fdl.WindowBinSize.MONTH,
            offset_delta=1  # 1 month offset
        ).create()

    Attributes:
        STATIC: Fixed baseline using historical reference data or specific time ranges
        ROLLING: Dynamic sliding window baseline that shifts with time
    """
    STATIC = 'STATIC'
    ROLLING = 'ROLLING'


@enum.unique
class WindowBinSize(str, enum.Enum):
    """
    Time granularities for rolling baseline window aggregation.

    Window bin sizes define the time intervals used for rolling baseline calculations.
    They determine how far back in time the rolling baseline looks and at what
    granularity the data is aggregated. This parameter is only used with rolling
    baselines and works in conjunction with offset_delta.

    Rolling Baseline Mechanics:
        - Window bin size sets the granularity of the sliding window
        - offset_delta determines how many bins to look back
        - Together they define the rolling window: offset_delta × window_bin_size
        - Example: WEEK + offset_delta=4 creates a 4-week rolling window

    Granularity Trade-offs:
        - **Finer granularity (HOUR)**: More responsive to recent changes, higher sensitivity
        - **Coarser granularity (MONTH)**: More stable patterns, reduced noise
        - **Medium granularity (DAY/WEEK)**: Balanced responsiveness and stability

    Selection Guidelines:
        - HOUR: High-frequency models with rapid data changes
        - DAY: Standard operational monitoring for most models
        - WEEK: Weekly business cycles, batch processing patterns
        - MONTH: Long-term trends, seasonal patterns, strategic monitoring

    Example:
        # Daily rolling baseline looking back 30 days
        daily_rolling = fdl.Baseline(
            name="daily_rolling_baseline",
            model_id=model.id,
            environment=fdl.EnvType.PRODUCTION,
            type_=fdl.BaselineType.ROLLING,
            window_bin_size=fdl.WindowBinSize.DAY,
            offset_delta=30
        ).create()

        # Weekly rolling baseline looking back 8 weeks
        weekly_rolling = fdl.Baseline(
            name="weekly_rolling_baseline",
            model_id=model.id,
            environment=fdl.EnvType.PRODUCTION,
            type_=fdl.BaselineType.ROLLING,
            window_bin_size=fdl.WindowBinSize.WEEK,
            offset_delta=8
        ).create()

    Data Volume Considerations:
        - Ensure sufficient data volume within each bin for statistical reliability
        - Finer granularities require higher prediction frequencies
        - Consider your model's prediction patterns when selecting bin size
        - Balance between responsiveness and statistical stability

    Attributes:
        HOUR: Hourly time bins for high-frequency rolling baselines
        DAY: Daily time bins for standard rolling baseline monitoring
        WEEK: Weekly time bins for trend analysis and batch patterns
        MONTH: Monthly time bins for long-term seasonal pattern detection
    """
    HOUR = 'Hour'
    DAY = 'Day'
    WEEK = 'Week'
    MONTH = 'Month'
