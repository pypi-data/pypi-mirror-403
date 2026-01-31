"""
Job entity for managing asynchronous operations in Fiddler.

The Job class represents long-running asynchronous operations in the Fiddler platform,
such as data publishing, model artifact uploads, surrogate model training, and other
operations that may take significant time to complete.

Key Concepts:
    - **Async Operations**: Handle long-running tasks without blocking
    - **Status Tracking**: Monitor job progress and completion states
    - **Error Handling**: Capture and report operation failures
    - **Progress Monitoring**: Real-time progress updates for running jobs
    - **Timeout Management**: Configurable timeouts for job completion

Job Lifecycle:
    1. **Creation**: Job created when async operation is initiated
    2. **Pending**: Job queued and waiting to start execution
    3. **Started**: Job actively executing with progress updates
    4. **Completion**: Job finishes with SUCCESS, FAILURE, or REVOKED status
    5. **Monitoring**: Track status, progress, and handle errors

Job Status Types:
    - **PENDING**: Job queued and waiting to start
    - **STARTED**: Job actively running with progress updates
    - **SUCCESS**: Job completed successfully
    - **FAILURE**: Job failed with error information
    - **RETRY**: Job being retried after failure
    - **REVOKED**: Job cancelled or terminated

Common Use Cases:
    - **Data Publishing**: Monitor large dataset upload progress
    - **Model Artifacts**: Track model deployment and artifact uploads
    - **Surrogate Training**: Monitor surrogate model training progress
    - **Batch Operations**: Handle bulk data processing jobs

Example:
    # Start an async operation (returns Job)
    job = model.publish(source="large_dataset.csv")
    print(f"Job started: {job.id}")

    # Wait for completion
    job.wait(timeout=3600)  # 1 hour timeout
    print("Data publishing completed!")

    # Monitor progress in real-time
    for job_update in job.watch(interval=30):
        print(f"Progress: {job_update.progress:.1f}%")
        if job_update.status == JobStatus.SUCCESS:
            break

Note:
    Jobs are automatically created by async operations and cannot be created
    directly. Use Job.get() to retrieve existing jobs and the watch/wait
    methods to monitor progress and completion.
"""
from __future__ import annotations

import logging
import time
from typing import Iterator
from uuid import UUID

import requests

from fiddler.configs import JOB_POLL_INTERVAL, JOB_WAIT_TIMEOUT
from fiddler.constants.job import JobStatus
from fiddler.decorators import handle_api_error
from fiddler.entities.base import BaseEntity
from fiddler.exceptions import AsyncJobFailed
from fiddler.schemas.job import JobResp

logger = logging.getLogger(__name__)


class Job(BaseEntity):  # pylint: disable=too-many-instance-attributes
    """Represents an asynchronous operation in the Fiddler platform.

    A Job tracks the execution of long-running operations such as data publishing,
    model artifact uploads, surrogate model training, and other async tasks. Jobs
    provide status monitoring, progress tracking, and error handling for operations
    that may take significant time to complete.

    Key Features:
        - **Status Monitoring**: Real-time tracking of job execution state
        - **Progress Tracking**: Percentage completion for running operations
        - **Error Reporting**: Detailed error messages and failure reasons
        - **Timeout Handling**: Configurable timeouts for job completion
        - **Responsive Polling**: Efficient status checking with backoff strategies

    Job States:
        - **PENDING**: Job queued and waiting to start execution
        - **STARTED**: Job actively running with progress updates
        - **SUCCESS**: Job completed successfully
        - **FAILURE**: Job failed with detailed error information
        - **RETRY**: Job being retried after a failure
        - **REVOKED**: Job cancelled or terminated

    Attributes:
        id (UUID, optional): Unique job identifier, assigned by server.
        name (str, optional): Human-readable job name describing the operation.
        status (str, optional): Current job status (PENDING, STARTED, SUCCESS, etc.).
        progress (float, optional): Completion percentage (0.0 to 100.0).
        info (dict, optional): Additional job information and metadata.
        error_message (str, optional): Detailed error message if job failed.
        error_reason (str, optional): High-level error category or reason.
        extras (dict, optional): Additional job-specific data and context.

    Example:
        # Get a job by ID
        job = Job.get(id_="550e8400-e29b-41d4-a716-446655440000")
        print(f"Job: {job.name} - Status: {job.status}")
        print(f"Progress: {job.progress:.1f}%")

        # Wait for job completion
        job.wait(timeout=1800)  # 30 minute timeout
        print("Job completed successfully!")

        # Monitor job progress in real-time
        for job_update in job.watch(interval=10, timeout=3600):
            print(f"{job_update.name}: {job_update.progress:.1f}%")
            if job_update.status in [JobStatus.SUCCESS, JobStatus.FAILURE]:
                break

    Note:
        Jobs are created automatically by async operations and cannot be instantiated
        directly. Use Job.get() to retrieve existing jobs and the monitoring methods
        to track progress and handle completion.
    """
    def __init__(self) -> None:
        """Initialize a Job instance.

        Creates a job object for tracking asynchronous operations. This constructor
        is typically used internally when deserializing API responses rather than
        for direct job creation.

        Note:
            Jobs are automatically created by async operations (like Model.publish(),
            Model.add_artifact(), etc.) and cannot be created directly. Use Job.get()
            to retrieve existing jobs and monitoring methods to track progress.
        """
        self.name: str | None = None
        self.status: str | None = None
        self.progress: float | None = None
        self.info: dict | None = None
        self.error_message: str | None = None
        self.error_reason: str | None = None
        self.extras: dict | None = None

        self.id: UUID | None = None

        # Deserialized response object
        self._resp: JobResp | None = None

    @classmethod
    def _from_dict(cls, data: dict) -> Job:
        """Build entity object from the given dictionary"""

        # Deserialize the response
        resp_obj = JobResp(**data)

        # Initialize
        instance = cls()

        # Add remaining fields
        fields = [
            'id',
            'name',
            'progress',
            'status',
            'info',
            'error_message',
            'error_reason',
            'extras',
        ]
        for field in fields:
            setattr(instance, field, getattr(resp_obj, field, None))

        instance._resp = resp_obj

        return instance

    def _refresh(self, data: dict) -> None:
        """Refresh the fields of this instance from the given response dictionary"""
        # Deserialize the response
        resp_obj = JobResp(**data)

        # Add remaining fields
        fields = [
            'id',
            'name',
            'progress',
            'status',
            'info',
            'error_message',
            'error_reason',
            'extras',
        ]
        for field in fields:
            setattr(self, field, getattr(resp_obj, field, None))

        self._resp = resp_obj

    @staticmethod
    def _get_url(id_: UUID | str | None = None) -> str:
        """Get job resource/item url"""
        url = '/v3/jobs'
        return url if not id_ else f'{url}/{id_}'

    @classmethod
    @handle_api_error
    def get(cls, id_: UUID | str, verbose: bool = False) -> Job:
        """Retrieve a job by its unique identifier.

        Fetches a job from the Fiddler platform using its UUID. This is the primary
        way to retrieve job information for monitoring async operations.

        Args:
            id_: The unique identifier (UUID) of the job to retrieve.
                Can be provided as a UUID object or string representation.
            verbose: Whether to include detailed task execution information.
                   When True, provides additional debugging and progress details.

        Returns:
            :class:`~fiddler.entities.Job`: The job instance with current status, progress, and metadata.

        Raises:
            NotFound: If no job exists with the specified ID.
            ApiError: If there's an error communicating with the Fiddler API.

        Example:
            # Get basic job information
            job = Job.get(id_="550e8400-e29b-41d4-a716-446655440000")
            print(f"Job: {job.name} - Status: {job.status}")
            print(f"Progress: {job.progress:.1f}%")

            # Get detailed job information for debugging
            detailed_job = Job.get(
                id_="550e8400-e29b-41d4-a716-446655440000",
                verbose=True
            )
            print(f"Task details: {detailed_job.info}")

            # Check for errors
            if job.status == JobStatus.FAILURE:
                print(f"Error: {job.error_reason}")
                print(f"Details: {job.error_message}")

        Note:
            This method makes an API call to fetch the latest job state from the server.
            Use verbose=True when debugging failed jobs to get additional task details.
        """
        response = cls._client().get(
            url=cls._get_url(id_=id_), params={'verbose': verbose}
        )
        return cls._from_response(response=response)

    def watch(
        self, interval: int = JOB_POLL_INTERVAL, timeout: int = JOB_WAIT_TIMEOUT
    ) -> Iterator[Job]:
        """Monitor job progress with real-time status updates.

        Continuously polls the job status at specified intervals and yields updated
        job instances. This method provides real-time monitoring of job progress
        and automatically handles network errors and retries.

        Args:
            interval: Polling interval in seconds between status checks.
                     Default is configured by JOB_POLL_INTERVAL (typically 5-10 seconds).
            timeout: Maximum time in seconds to monitor the job before giving up.
                    Default is configured by JOB_WAIT_TIMEOUT (typically 1800 seconds).

        Yields:
            :class:`~fiddler.entities.Job`: Updated job instances with current status and progress.

        Raises:
            TimeoutError: If the job doesn't complete within the specified timeout.
            AsyncJobFailed: If the job fails during execution (raised by wait() method).

        Example:
            # Monitor job progress with default settings
            job = model.publish(source="large_dataset.csv")
            for job_update in job.watch():
                print(f"Progress: {job_update.progress:.1f}%")
                print(f"Status: {job_update.status}")
                if job_update.status in [JobStatus.SUCCESS, JobStatus.FAILURE]:
                    break

            # Custom polling interval and timeout
            for job_update in job.watch(interval=30, timeout=7200):  # 2 hour timeout
                print(f"{job_update.name}: {job_update.progress:.1f}%")
                if job_update.status == JobStatus.SUCCESS:
                    print("Job completed successfully!")
                    break
                elif job_update.status == JobStatus.FAILURE:
                    print(f"Job failed: {job_update.error_message}")
                    break

            # Progress tracking with custom logic
            last_progress = 0
            for job_update in job.watch(interval=15):
                if job_update.progress > last_progress + 10:
                    print(f"Progress milestone: {job_update.progress:.1f}%")
                    last_progress = job_update.progress

        Note:
            This method handles network errors gracefully and continues monitoring.
            It automatically stops when the job reaches a terminal state (SUCCESS,
            FAILURE, or REVOKED). Use shorter intervals for more responsive monitoring
            but be mindful of API rate limits.
        """
        assert self.id is not None
        deadline = time.monotonic() + timeout

        while True:
            if time.monotonic() > deadline:
                raise TimeoutError(f'Deadline exceeded while watching job {self.id}')

            try:
                # This can raise requests.HTTPError to represent non-2xx
                # responses.
                response = self._client().get(
                    url=self._get_url(id_=self.id),
                    # Short-ish TCP connect timeout, to stay responsive in
                    # terms of logging. The HTTP response latency for GET
                    # /jobs/<id> is expected to be less than couple of seconds
                    # (i.e., 30 s includes lots of  leeway).
                    timeout=(5, 30),
                    # Inject `retry="off"` to disable the centralized retry
                    # machinery: ask for being confronted with the details
                    # (throw exceptions my way, so I an do my own "responsive"
                    # type of retrying). Otherwise, we'd give up control.
                    retry='off',
                )
                self._refresh_from_response(response)

            except requests.exceptions.HTTPError as exc:
                # Note(JP): got a non-2xx HTTP response. The main purpose of
                # this handler is to keep going after having received a 5xx
                # response. In this case of GETting job status even some 404s
                # might be worth retrying. That is, it's fine to give up only
                # after reaching the deadline even if we collect some 4xx
                # responses along the way. Noteworthy: Receiving a 5xx response
                # here is not an error, it's an expected scenario to be
                # accounted for.
                logger.info(
                    'watch: ignore unexpected response %s (URL: %s, response body prefix: %s...)',
                    exc.response,
                    exc.request.url,
                    exc.response.text[:120],
                )
                continue

            except requests.exceptions.RequestException:
                # This error is in the hierarchy _above_ `HTTPError`, and in
                # this setup catches all errors that are _not_ a bad response:
                # DNS error, TCP connect timeout, err during sending request,
                # err during receiving response. Rely on the error detail to
                # have already been logged.
                continue

            yield self

            if self.status in [
                JobStatus.SUCCESS,
                JobStatus.FAILURE,
                JobStatus.REVOKED,
            ]:
                return

            time.sleep(interval)

    def wait(
        self, interval: int = JOB_POLL_INTERVAL, timeout: int = JOB_WAIT_TIMEOUT
    ) -> None:
        """Wait for job completion with automatic progress logging.

        Blocks execution until the job completes (successfully or with failure).
        Provides automatic progress logging and raises an exception if the job fails.
        This is the most convenient method for simple job completion waiting.

        Args:
            interval: Polling interval in seconds between status checks.
                     Default is configured by JOB_POLL_INTERVAL (typically 5-10 seconds).
            timeout: Maximum time in seconds to wait for job completion.
                    Default is configured by JOB_WAIT_TIMEOUT (typically 1800 seconds).

        Raises:
            TimeoutError: If the job doesn't complete within the specified timeout.
            AsyncJobFailed: If the job fails during execution, includes error details.

        Example:
            # Simple job completion waiting
            job = model.publish(source="training_data.csv")
            job.wait()  # Blocks until completion
            print("Data publishing completed!")

            # Custom timeout for long-running jobs
            job = model.add_artifact(model_dir="./model_package")
            job.wait(timeout=3600)  # 1 hour timeout
            print("Model artifact upload completed!")

            # Handle job failures
            try:
                job = model.publish(source="invalid_data.csv")
                job.wait()
            except AsyncJobFailed as e:
                print(f"Job failed: {e}")
                # Handle failure (retry, alert, etc.)

            # Fast polling for critical operations
            job = model.update_surrogate(dataset_id=dataset.id)
            job.wait(interval=5, timeout=600)  # 5 second polling, 10 min timeout

        Note:
            This method automatically logs progress updates to the logger. For custom
            progress handling, use the watch() method instead. The method blocks the
            current thread until completion, so consider using watch() for non-blocking
            monitoring in async applications.
        """
        log_prefix = f'{self.name}[{self.id}]'

        for job in self.watch(interval=interval, timeout=timeout):
            logger.info(
                '%s: %s, progress: %.1f%%',
                log_prefix,
                job.status,
                job.progress,
            )

            if job.status == JobStatus.SUCCESS:
                logger.info('%s: successfully completed', log_prefix)
            elif job.status == JobStatus.FAILURE:
                raise AsyncJobFailed(
                    f'{log_prefix} failed with {job.error_reason or "Exception"}: '
                    f'{job.error_message}'
                )
