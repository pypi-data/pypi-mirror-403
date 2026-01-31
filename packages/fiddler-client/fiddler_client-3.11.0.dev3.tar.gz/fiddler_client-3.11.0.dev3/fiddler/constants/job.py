"""Job status constants for Fiddler AI platform asynchronous operations.

This module defines job status constants used to track the lifecycle of asynchronous
operations in Fiddler. Jobs represent long-running tasks such as data publishing,
model artifact uploads, baseline creation, and explainability computations.

Key Concepts:
    - **Job Lifecycle**: Jobs progress through various states from creation to completion
    - **Asynchronous Operations**: Many Fiddler operations return Job objects for tracking
    - **Status Monitoring**: Job status can be monitored to determine operation progress
    - **Error Handling**: Failed jobs provide status information for troubleshooting

Common Job Operations:
    - Data publishing (model.publish())
    - Model artifact uploads
    - Baseline dataset creation
    - Explainability computations
    - Custom metric calculations

Usage Pattern:
    Jobs are typically returned from asynchronous operations and can be monitored:

    ```python
    import fiddler as fdl

    # Start an asynchronous operation
    job = model.publish(source=data, environment=fdl.EnvType.PRODUCTION)

    # Monitor job status
    while job.status in [fdl.JobStatus.PENDING, fdl.JobStatus.STARTED]:
        print(f"Job {job.id}: {job.status}")
        time.sleep(5)
        job.refresh()  # Update job status

    # Check final result
    if job.status == fdl.JobStatus.SUCCESS:
        print("Operation completed successfully")
    elif job.status == fdl.JobStatus.FAILURE:
        print(f"Operation failed: {job.error_message}")
    ```

See Also:
    - :class:`~fiddler.entities.Job` for job management and monitoring
    - :class:`~fiddler.entities.Model` for operations that return jobs
    - Fiddler documentation on Jobs: https://docs.fiddler.ai/technical-reference/api-methods-30#jobs
"""

import enum


@enum.unique
class JobStatus(str, enum.Enum):
    """Status values for asynchronous job operations in Fiddler.

    This enum defines the possible states that a Job can be in during its lifecycle.
    Jobs represent asynchronous operations such as data publishing, model uploads,
    and computation tasks that may take significant time to complete.

    Job Lifecycle:
        1. **PENDING**: Job created and queued for execution
        2. **STARTED**: Job execution has begun
        3. **SUCCESS/FAILURE**: Job completed with final status
        4. **RETRY**: Job failed but will be retried automatically
        5. **REVOKED**: Job was cancelled before completion

    Attributes:
        PENDING: Job is queued and waiting to start
        STARTED: Job execution is in progress
        SUCCESS: Job completed successfully
        FAILURE: Job failed and will not be retried
        RETRY: Job failed but will be automatically retried
        REVOKED: Job was cancelled or revoked

    Examples:
        Monitoring job progress:

        ```python
        # Start a data publishing job
        job = model.publish(source=data_df, environment=fdl.EnvType.PRODUCTION)

        # Wait for completion
        job.wait()  # Blocks until job completes

        # Check final status
        if job.status == fdl.JobStatus.SUCCESS:
            print("Data published successfully")
        else:
            print(f"Job failed with status: {job.status}")
        ```

        Polling job status manually:

        ```python
        import time

        # Check status periodically
        while job.status in [fdl.JobStatus.PENDING, fdl.JobStatus.STARTED]:
            print(f"Job progress: {job.progress}%")
            time.sleep(10)
            job.refresh()  # Update job status from server

        # Handle different completion states
        if job.status == fdl.JobStatus.SUCCESS:
            print("Operation completed successfully")
        elif job.status == fdl.JobStatus.FAILURE:
            print(f"Operation failed: {job.error_message}")
        elif job.status == fdl.JobStatus.REVOKED:
            print("Operation was cancelled")
        ```

        Handling job failures and retries:

        ```python
        # Monitor job with retry handling
        max_wait_time = 3600  # 1 hour timeout
        start_time = time.time()

        while (time.time() - start_time) < max_wait_time:
            if job.status == fdl.JobStatus.SUCCESS:
                break
            elif job.status == fdl.JobStatus.FAILURE:
                print(f"Job failed permanently: {job.error_message}")
                break
            elif job.status == fdl.JobStatus.RETRY:
                print("Job failed but will be retried automatically")

            time.sleep(30)
            job.refresh()
        ```

    Note:
        Job status should be refreshed periodically using job.refresh() to get
        the latest status from the server. The job.wait() method provides a
        convenient way to block until completion.
    """

    PENDING = 'PENDING'
    """Job is queued and waiting to start execution.

    This is the initial status when a job is first created. The job has been
    submitted to the system but has not yet begun processing. Jobs may remain
    in PENDING status if there are resource constraints or if they are waiting
    for dependencies.

    Characteristics:
    - Job is in the execution queue
    - No processing has started yet
    - May transition to STARTED when resources become available
    - Can be cancelled while in this state

    Typical duration: Seconds to minutes depending on system load
    """

    STARTED = 'STARTED'
    """Job execution is currently in progress.

    The job has begun processing and is actively running. Progress information
    may be available through the job.progress property. Jobs in this state
    are consuming system resources and performing the requested operation.

    Characteristics:
    - Active processing is occurring
    - Progress updates may be available
    - Cannot be cancelled once started
    - Will transition to SUCCESS, FAILURE, or RETRY

    Typical duration: Minutes to hours depending on operation complexity
    """

    SUCCESS = 'SUCCESS'
    """Job completed successfully.

    The operation has finished successfully and all requested work has been
    completed. Results are available and the operation achieved its intended
    outcome without errors.

    Characteristics:
    - Operation completed without errors
    - Results are available for use
    - Job will not change status again
    - Resources have been released

    This is a terminal status - the job is complete.
    """

    FAILURE = 'FAILURE'
    """Job failed and will not be retried.

    The operation encountered an error and could not be completed successfully.
    This is a permanent failure - the job will not be automatically retried.
    Error details are typically available in the job.error_message property.

    Characteristics:
    - Operation failed due to an error
    - No automatic retry will occur
    - Error details available in error_message
    - Manual intervention may be required

    Common causes:
    - Invalid input data or parameters
    - Insufficient permissions
    - System resource exhaustion
    - Data validation failures

    This is a terminal status - the job will not continue.
    """

    RETRY = 'RETRY'
    """Job failed but will be automatically retried.

    The operation encountered a temporary error but the system will automatically
    attempt to retry the job. This typically occurs for transient issues like
    network timeouts or temporary resource unavailability.

    Characteristics:
    - Temporary failure occurred
    - System will automatically retry
    - May transition back to PENDING or STARTED
    - Retry attempts are limited

    Common causes:
    - Network connectivity issues
    - Temporary resource constraints
    - Transient system errors
    - Database connection timeouts

    The job may eventually succeed or transition to FAILURE if retries are exhausted.
    """

    REVOKED = 'REVOKED'
    """Job was cancelled or revoked before completion.

    The job was explicitly cancelled by the user or system before it could
    complete. This may occur due to user cancellation, system shutdown, or
    administrative intervention.

    Characteristics:
    - Job was cancelled before completion
    - No results are available
    - Resources have been cleaned up
    - Operation did not complete

    Common causes:
    - User-initiated cancellation
    - System maintenance or shutdown
    - Administrative intervention
    - Timeout or resource limits exceeded

    This is a terminal status - the job will not continue.
    """
