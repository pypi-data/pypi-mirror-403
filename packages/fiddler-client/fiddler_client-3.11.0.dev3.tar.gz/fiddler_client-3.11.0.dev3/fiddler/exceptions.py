from __future__ import annotations

import logging
from http import HTTPStatus

from fiddler.schemas.response import ErrorData
from fiddler.version import __version__

logger = logging.getLogger(__name__)


class BaseError(Exception):
    """Base exception class for all Fiddler client errors.

    This is the parent class for all custom exceptions in the Fiddler client
    library. It provides common functionality for error handling, message
    formatting, and error identification.

    Attributes:
        message: Human-readable error message describing the issue
        name: Name of the specific error type (class name)

    Examples:
        Catching any Fiddler-specific error:

        try:
            # Some Fiddler operation
            pass
        except BaseError as e:
            print(f"Fiddler error occurred: {e.name} - {e.message}")
    """
    message: str = 'Something went wrong'

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)

    def __str__(self) -> str:
        # It would be better to prepend context: like FiddlerBaseError. Note
        # that this here is the string representation of an exception.
        return str(self.message)

    @property
    def name(self) -> str:
        """Name of the error type."""
        return self.__class__.__name__


class IncompatibleClient(BaseError):  # noqa: N818
    """Raised when the Python client version is incompatible with the Fiddler platform version.

    This exception occurs during connection initialization when the client library
    version is not compatible with the connected Fiddler platform version. This
    ensures that users are aware of version mismatches that could cause unexpected
    behavior or missing functionality.

    The exception includes both the client version and server version in the error
    message to help users understand what versions are involved in the incompatibility.

    Attributes:
        message: Formatted message showing both client and server versions

    Examples:
        Handling version incompatibility:

        try:
            fdl.init(url="https://old-fiddler.com", token="token")
        except IncompatibleClient as e:
            print(f"Version mismatch: {e.message}")
            # Upgrade client or contact administrator

        Typical error message format:
        "Python Client version (3.8.0) is not compatible with your
        Fiddler Platform version (3.5.0)."
    """

    message = (
        'Python Client version ({client_version}) is not compatible with your '
        'Fiddler Platform version ({server_version}).'
        # @TODO - Add link to compatibility matrix doc
    )

    def __init__(self, server_version: str, message: str | None = None) -> None:
        self.message = message or self.message.format(
            client_version=__version__, server_version=server_version
        )

        super().__init__(self.message)


class AsyncJobFailed(BaseError):  # noqa: N818
    """Raised when an asynchronous job fails to execute successfully.

    This exception is thrown when long-running operations (such as model training,
    data processing, or batch operations) fail to complete successfully. The job
    may have been submitted successfully but encountered an error during execution.

    Async jobs in Fiddler include operations like model artifact uploads, baseline
    computations, batch data ingestion, and other time-intensive operations that
    run in the background.

    Examples:
        Handling async job failures:

        try:
            job = model.upload_artifact(artifact_path)
            job.wait()  # Wait for completion
        except AsyncJobFailed as e:
            print(f"Job failed: {e.message}")
            # Check job logs or retry operation

        Monitoring job status to avoid exceptions:

        job = model.upload_artifact(artifact_path)
        while not job.is_complete():
            if job.status == JobStatus.FAILED:
                print(f"Job failed: {job.error_message}")
                break
            time.sleep(5)
    """


class Unsupported(BaseError):  # noqa: N818
    """Raised when an unsupported operation is attempted.

    This exception occurs when users try to perform operations that are not
    supported by the current Fiddler platform configuration, client version,
    or specific model/dataset setup. This can include feature limitations,
    deprecated functionality, or operations not available for certain model types.

    Common scenarios include attempting to use features not available in the
    current platform edition, trying deprecated API methods, or performing
    operations incompatible with the model's configuration.

    Attributes:
        message: Description of the unsupported operation

    Examples:
        Handling unsupported operations:

        try:
            model.enable_advanced_feature()
        except Unsupported as e:
            print(f"Feature not available: {e.message}")
            # Use alternative approach or upgrade platform

        Common unsupported scenarios:
        - Using enterprise features on basic plans
        - Attempting operations on incompatible model types
        - Calling deprecated API methods
    """

    message = 'This operation is not supported'


class HttpError(BaseError):
    """Base class for all HTTP-related errors.

    This is the parent class for HTTP communication errors that can occur
    during API requests to the Fiddler platform. While this specific class
    is deprecated and no longer thrown directly, it serves as the base for
    more specific HTTP error types.

    Note:
        This class is deprecated and not thrown anymore. Use more specific
        HTTP error subclasses like ApiError, NotFound, or Conflict instead.

    Examples:
        Catching any HTTP-related error:

        try:
            # API operation
            pass
        except HttpError as e:
            print(f"HTTP error: {e.message}")
    """


class ConnTimeout(HttpError):  # noqa: N818
    """Raised when a connection timeout occurs during HTTP requests.

    This exception was used to indicate that an HTTP request to the Fiddler
    platform timed out while waiting for a response. Timeouts can occur due
    to network issues, server overload, or requests taking longer than the
    configured timeout period.

    Note:
        This class is deprecated and not thrown anymore. The client now
        handles timeouts through the underlying HTTP client with automatic
        retry mechanisms.

    Attributes:
        message: Timeout-specific error message

    Examples:
        Historical usage (now deprecated):

        try:
            # Long-running API call
            pass
        except ConnTimeout as e:
            print(f"Request timed out: {e.message}")
            # Retry with longer timeout or check network
    """

    message = 'Request timed out while trying to reach endpoint'


class ConnError(HttpError):
    """Raised when a connection error occurs during HTTP requests.

    This exception was used to indicate general connection problems when
    trying to communicate with the Fiddler platform, such as network
    unreachability, DNS resolution failures, or connection refused errors.

    Note:
        This class is deprecated and not thrown anymore. The client now
        handles connection errors through the underlying HTTP client with
        automatic retry mechanisms and more specific error reporting.

    Attributes:
        message: Connection-specific error message

    Examples:
        Historical usage (now deprecated):

        try:
            # Network API call
            pass
        except ConnError as e:
            print(f"Connection failed: {e.message}")
            # Check network connectivity or URL configuration
    """

    message = 'Unable to reach the given endpoint'


class ApiError(HttpError):
    """Raised when the Fiddler API returns an HTTP error response.

    This exception represents errors returned by the Fiddler platform API,
    including both client errors (4xx status codes) and server errors
    (5xx status codes). It contains detailed information about the error
    including the HTTP status code, error message, and any additional
    error details provided by the API.

    ApiError serves as the base class for more specific API errors like
    NotFound and Conflict, but can also be raised directly for other
    HTTP error status codes.

    Attributes:
        code: HTTP status code returned by the API
        message: Error message from the API response
        errors: Additional error details from the API (if any)
        reason: Human-readable reason for the error

    Examples:
        Handling general API errors:

        try:
            model = client.get_model("nonexistent-model")
        except ApiError as e:
            print(f"API Error {e.code}: {e.message}")
            if e.errors:
                print(f"Details: {e.errors}")

        Handling specific status codes:

        try:
            # API operation
            pass
        except ApiError as e:
            if e.code == 429:  # Rate limit
                print("Rate limited, retrying later...")
                time.sleep(60)
            elif e.code >= 500:  # Server error
                print("Server error, contact support")
            else:
                print(f"Client error: {e.message}")
    """

    code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    reason: str = 'ApiError'

    def __init__(self, error: ErrorData) -> None:
        self.code = error.code
        self.message = error.message
        self.errors = error.errors
        super().__init__(self.message)


class NotFound(ApiError):  # noqa: N818
    """Raised when a requested resource is not found (HTTP 404).

    This exception is thrown when attempting to access or manipulate a resource
    that does not exist in the Fiddler platform. This can include models,
    projects, datasets, alerts, or any other entity that cannot be located
    using the provided identifier.

    Common scenarios include using incorrect IDs, attempting to access deleted
    resources, or referencing resources that haven't been created yet.

    Attributes:
        code: Always set to 404 (HTTP_NOT_FOUND)
        reason: Always set to 'NotFound'
        message: Specific error message about what resource was not found

    Examples:
        Handling missing resources:

        try:
            model = client.get_model("wrong-model-id")
        except NotFound as e:
            print(f"Model not found: {e.message}")
            # Create the model or check the correct ID

        Checking if a resource exists:

        try:
            project = client.get_project("my-project")
            print("Project exists")
        except NotFound:
            print("Project doesn't exist, creating it...")
            project = client.create_project(name="my-project")

        Common NotFound scenarios:
        - Accessing models, projects, or datasets with wrong IDs
        - Referencing deleted or expired resources
        - Typos in resource names or identifiers
    """
    code: int = HTTPStatus.NOT_FOUND
    reason: str = 'NotFound'


class Conflict(ApiError):  # noqa: N818
    """Raised when a request conflicts with the current state of a resource (HTTP 409).

    This exception occurs when attempting to perform an operation that conflicts
    with the current state of a resource. This typically happens when trying to
    create resources that already exist, or when concurrent modifications cause
    state conflicts.

    Common scenarios include creating models or projects with names that already
    exist, attempting to modify resources that are currently being processed,
    or violating business rules that prevent certain operations.

    Attributes:
        code: Always set to 409 (HTTP_CONFLICT)
        reason: Always set to 'Conflict'
        message: Specific error message about the conflict

    Examples:
        Handling resource conflicts:

        try:
            project = client.create_project(name="existing-project")
        except Conflict as e:
            print(f"Project already exists: {e.message}")
            # Use existing project or choose different name
            project = client.get_project("existing-project")

        Handling state conflicts:

        try:
            model.update_status("active")
        except Conflict as e:
            print(f"Cannot change status: {e.message}")
            # Wait for current operation to complete

        Common Conflict scenarios:
        - Creating resources with duplicate names
        - Modifying resources during processing
        - Violating business logic constraints
        - Concurrent modification conflicts
    """
    code: int = HTTPStatus.CONFLICT
    reason: str = 'Conflict'
