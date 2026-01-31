from __future__ import annotations

import logging
import sys
from functools import cached_property
from uuid import UUID

import fiddler.utils.logger
from fiddler.configs import MIN_SERVER_VERSION
from fiddler.constants.common import (
    CLIENT_NAME,
    FIDDLER_CLIENT_NAME_HEADER,
    FIDDLER_CLIENT_VERSION_HEADER,
    FIDDLER_PYTHON_VERSION_HEADER,
)
from fiddler.decorators import handle_api_error
from fiddler.exceptions import IncompatibleClient
from fiddler.libs.http_client import RequestClient
from fiddler.schemas.server_info import ServerInfo, Version
from fiddler.utils.version import match_semver
from fiddler.version import __version__

log = logging.getLogger(__name__)


class Connection:
    """Manages authenticated connections to the Fiddler platform.

    The Connection class handles all aspects of connecting to and communicating
    with the Fiddler platform, including authentication, HTTP client management,
    server version compatibility checking, and organization context management.

    This class provides the foundation for all API interactions with Fiddler,
    managing connection parameters, authentication tokens, and ensuring proper
    communication protocols are established.

    Attributes:
        url: Base URL of the Fiddler platform instance
        token: Authentication token for API access
        proxies: Optional proxy configuration for HTTP requests
        timeout: HTTP request timeout settings
        verify: Whether to verify SSL/TLS certificates
        request_headers: HTTP headers including authentication and client info
        client: Cached HTTP client instance for making requests
        server_info: Cached server information and metadata
        server_version: Version of the connected Fiddler server
        organization_name: Name of the connected organization
        organization_id: UUID of the connected organization

    Examples:
        Creating a basic connection:

        connection = Connection(
            url="https://your-fiddler-instance.com",
            token="your-auth-token"
        )

        Creating a connection with custom timeout and proxy:

        connection = Connection(
            url="https://your-fiddler-instance.com",
            token="your-auth-token",
            timeout=(5.0, 30.0),  # (connect_timeout, read_timeout)
            proxies={"https": "https://proxy.company.com:8080"}
        )

        Creating a connection without SSL verification:

        connection = Connection(
            url="https://your-fiddler-instance.com",
            token="your-auth-token",
            verify=False,  # Not recommended for production
            validate=False  # Skip version compatibility check
        )
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        url: str,
        token: str,
        proxies: dict | None = None,
        timeout: float | tuple[float, float] | None = None,
        verify: bool = True,
        validate: bool = True,
    ) -> None:
        """Initialize a connection to the Fiddler platform.

        Args:
            url: The base URL to your Fiddler platform instance
            token: Authentication token obtained from the Fiddler UI
            proxies: Dictionary mapping protocol to proxy URL for HTTP requests
            timeout: HTTP request timeout settings (float or tuple of connect/read timeouts)
            verify: Whether to verify server's TLS certificate (default: True)
            validate: Whether to validate server/client version compatibility (default: True)

        Raises:
            ValueError: If url or token parameters are empty
            IncompatibleClient: If server version is incompatible with client version
        """

        self.url = url
        self.token = token
        self.proxies = proxies
        self.timeout = timeout
        self.verify = verify

        if not url:
            raise ValueError('`url` is empty')

        if not token:
            raise ValueError('`token` is empty')

        python_version = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        self.request_headers = {
            'Authorization': f'Bearer {token}',
            FIDDLER_CLIENT_NAME_HEADER: CLIENT_NAME,
            FIDDLER_CLIENT_VERSION_HEADER: __version__,
            FIDDLER_PYTHON_VERSION_HEADER: python_version,
        }

        if validate:
            self._check_server_version()
            self._check_version_compatibility()

    @cached_property
    def client(self) -> RequestClient:
        """Get the HTTP request client instance for API communication.

        Returns:
            RequestClient: Configured HTTP client with authentication headers,
            proxy settings, and timeout configurations.
        """
        return RequestClient(
            base_url=self.url,
            headers=self.request_headers,
            proxies=self.proxies,
            verify=self.verify,
            timeout_override=self.timeout,
        )

    @cached_property
    def server_info(self) -> ServerInfo:
        """Get server information and metadata from the Fiddler platform.

        Returns:
            ServerInfo: Server information including version, organization details,
            and platform configuration.
        """
        return self._get_server_info()

    @cached_property
    def server_version(self) -> Version:
        """Get the semantic version of the connected Fiddler server.

        Returns:
            Version: Semantic version object representing the server version.
        """
        return self.server_info.server_version

    @cached_property
    def organization_name(self) -> str:
        """Get the name of the connected organization.

        Returns:
            str: Name of the organization associated with this connection.
        """
        return self.server_info.organization.name

    @cached_property
    def organization_id(self) -> UUID:
        """Get the UUID of the connected organization.

        Returns:
            UUID: Unique identifier of the organization associated with this connection.
        """
        return self.server_info.organization.id

    @handle_api_error
    def _get_server_info(self) -> ServerInfo:
        """Retrieve server information from the Fiddler platform.

        Returns:
            ServerInfo: Server information including version and organization details.

        Raises:
            ApiError: If the server info request fails.
        """

        # Tight-ish timeout.
        response = self.client.get(url='/v3/server-info', timeout=(5, 15))

        return ServerInfo(**response.json().get('data'))

    @handle_api_error
    def _check_version_compatibility(self) -> None:
        """Check whether the client version is compatible with the Fiddler platform version.

        Raises:
            ApiError: If the version compatibility check fails.
            IncompatibleClient: If the client version is not compatible with the server.
        """

        self.client.get(
            url='/v3/version-compatibility',
            params={
                'client_version': __version__,
                'client_name': CLIENT_NAME,
            },
            timeout=(5, 15),
        )

    def _check_server_version(self) -> None:
        """Check whether the Fiddler platform version is compatible with the client version.

        Raises:
            IncompatibleClient: If the server version is below the minimum required version.
        """
        if match_semver(self.server_version, f'>={MIN_SERVER_VERSION}'):
            return

        raise IncompatibleClient(server_version=str(self.server_version))


class ConnectionMixin:
    """Mixin class providing connection-related functionality to other classes.

    ConnectionMixin provides a standardized way for other classes to access
    the global Fiddler connection instance and its associated properties.
    This mixin enables classes throughout the Fiddler client to access
    connection details, HTTP client functionality, and organization context
    without directly managing connection state.

    This pattern ensures consistent access to connection resources across
    all client components while maintaining a clean separation of concerns.

    Methods:
        _conn: Access to the global Connection instance
        _client: Access to the HTTP client for API requests
        organization_name: Property access to organization name
        organization_id: Property access to organization UUID
        get_organization_name: Class method to retrieve organization name
        get_organization_id: Class method to retrieve organization UUID

    Examples:
        Using ConnectionMixin in a custom class:

        class CustomModel(ConnectionMixin):
            def fetch_data(self):
                # Access HTTP client through mixin
                response = self._client().get('/api/data')
                return response.json()

            def get_org_info(self):
                # Access organization info through mixin
                return {
                    'name': self.organization_name,
                    'id': str(self.organization_id)
                }

        Using class methods without instantiation:

        org_name = SomeEntityClass.get_organization_name()
        org_id = SomeEntityClass.get_organization_id()
    """

    @classmethod
    def _conn(cls) -> Connection:
        """Get the global Fiddler connection instance.

        Returns:
            Connection: The singleton Connection instance used throughout the client.

        Raises:
            AssertionError: If no connection has been initialized via fiddler.init().
        """
        from fiddler import conn  # pylint: disable=import-outside-toplevel

        assert conn is not None
        return conn

    @classmethod
    def _client(cls) -> RequestClient:
        """Get the HTTP request client from the global connection.

        Returns:
            RequestClient: HTTP client instance for making API requests.
        """
        return cls._conn().client

    @property
    def organization_name(self) -> str:
        """Get the organization name from the connection.

        Returns:
            str: Name of the organization associated with the current connection.
        """
        return self._conn().server_info.organization.name

    @property
    def organization_id(self) -> UUID:
        """Get the organization UUID from the connection.

        Returns:
            UUID: Unique identifier of the organization associated with the current connection.
        """
        return self._conn().server_info.organization.id

    @classmethod
    def get_organization_name(cls) -> str:
        """Get the organization name from the global connection.

        Returns:
            str: Name of the organization associated with the current connection.
        """
        return cls._conn().server_info.organization.name

    @classmethod
    def get_organization_id(cls) -> UUID:
        """Get the organization UUID from the global connection.

        Returns:
            UUID: Unique identifier of the organization associated with the current connection.
        """
        return cls._conn().server_info.organization.id


def init(  # pylint: disable=too-many-arguments
    url: str,
    token: str,
    proxies: dict | None = None,
    timeout: float | tuple[float, float] | None = None,
    verify: bool = True,
    validate: bool = True,
    auto_attach_log_handler: bool = True,
) -> None:
    """Initialize the Fiddler client with connection parameters and global configuration.

    This function establishes a connection to the Fiddler platform and configures
    the global client state. It handles authentication, server compatibility
    validation, logging setup, and creates the singleton connection instance
    used throughout the client library.

    The function also configures automatic retry strategies for HTTP requests,
    sets up logging handlers if needed, and supports AWS SageMaker partner
    application authentication.

    Args:
        url: The base URL to your Fiddler platform instance
        token: Authentication token obtained from the Fiddler UI Credentials tab
        proxies: Dictionary mapping protocol to proxy URL for HTTP requests
        timeout: HTTP request timeout settings (float or tuple of connect/read timeouts)
        verify: Whether to verify server's TLS certificate (default: True)
        validate: Whether to validate server/client version compatibility (default: True)
        auto_attach_log_handler: Whether to automatically attach log handler to stderr (default: True)

    Raises:
        ValueError: If url or token parameters are empty
        IncompatibleClient: If server version is incompatible with client version
        ConnectionError: If unable to connect to the Fiddler platform

    Examples:
        Basic initialization:

        import fiddler as fdl

        fdl.init(
            url="https://your-fiddler-instance.com",
            token="your-auth-token"
        )

        Initialization with custom timeout and proxy:

        fdl.init(
            url="https://your-fiddler-instance.com",
            token="your-auth-token",
            timeout=(10.0, 60.0),  # 10s connect, 60s read timeout
            proxies={"https": "https://proxy.company.com:8080"}
        )

        Initialization for development with relaxed settings:

        fdl.init(
            url="https://dev-fiddler-instance.com",
            token="dev-token",
            verify=False,  # Skip SSL verification
            validate=False,  # Skip version compatibility check
            auto_attach_log_handler=False  # Custom logging setup
        )

        AWS SageMaker partner app initialization:

        import os
        os.environ["AWS_PARTNER_APP_AUTH"] = "true"
        os.environ["AWS_PARTNER_APP_ARN"] = "your-partner-app-arn"
        os.environ["AWS_PARTNER_APP_URL"] = "your-partner-app-url"

        fdl.init(
            url="https://your-fiddler-instance.com",
            token="sagemaker-token"
        )

    Note:
        The client implements automatic retry strategies for transient failures.
        Configure retry duration via FIDDLER_CLIENT_RETRY_MAX_DURATION_SECONDS
        environment variable (default: 300 seconds).

        Logging is performed under the 'fiddler' namespace at INFO level.
        If no root logger is configured, a stderr handler is automatically
        attached unless auto_attach_log_handler=False.
    """
    from fiddler import _set_conn  # pylint: disable=import-outside-toplevel

    # If this library is imported into an interpreter that has a root logger
    # configured (with handler(s) attached) then just propagate log messages
    # into that hierarchy, and do not attach a handler to the 'fiddler' logger.
    if not logging.getLogger().handlers and auto_attach_log_handler:
        fiddler.utils.logger._attach_handler()
        log.info(
            'attached stderr handler to logger: auto_attach_log_handler=True, and root logger not configured'
        )

    # Singleton object in Python interpreter.
    conn = Connection(
        url=url,
        token=token,
        proxies=proxies,
        timeout=timeout,
        verify=verify,
        validate=validate,
    )

    _set_conn(conn_=conn)
