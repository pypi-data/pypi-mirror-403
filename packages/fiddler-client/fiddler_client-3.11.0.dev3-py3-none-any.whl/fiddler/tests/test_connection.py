from http import HTTPStatus
import sys
from uuid import UUID

import pytest
import responses
from responses import matchers

from fiddler.connection import Connection
from fiddler.constants.common import CLIENT_NAME, FIDDLER_PYTHON_VERSION_HEADER
from fiddler.exceptions import ApiError
from fiddler.schemas.server_info import ServerInfo
from fiddler.tests.constants import ORG_ID, ORG_NAME, URL
from fiddler.version import __version__

SERVER_INFO_API_RESPONSE = {
    'data': {
        'server_version': '24.1.0-pre-3e889ef',
        'feature_flags': {},
        'organization': {'id': ORG_ID, 'name': ORG_NAME},
    },
    'api_version': '3.0',
    'kind': 'NORMAL',
}


@responses.activate
def test_version_compatibility_success(connection: Connection) -> None:
    params = {'client_name': CLIENT_NAME, 'client_version': __version__}
    responses.get(
        url=f'{URL}/v3/version-compatibility',
        match=[
            matchers.query_param_matcher(params),
            matchers.header_matcher(
                {
                    'Authorization': 'Bearer footoken',
                    'X-Fiddler-Client-Name': 'python-sdk',
                    'X-Fiddler-Client-Version': __version__,
                }
            ),
        ],
    )

    connection._check_version_compatibility()


@responses.activate
def test_version_compatibility_failed(connection: Connection) -> None:
    responses.get(
        url=f'{URL}/v3/version-compatibility',
        json={
            'error': {
                'code': HTTPStatus.BAD_REQUEST,
                'message': 'You are using old fiddler-client version. Please upgrade to 3.x or above',
                'errors': [],
            }
        },
        status=HTTPStatus.BAD_REQUEST,
    )

    with pytest.raises(ApiError):
        connection._check_version_compatibility()


@responses.activate
def test_get_server_info(connection: Connection) -> None:
    responses.get(
        url=f'{URL}/v3/server-info',
        json=SERVER_INFO_API_RESPONSE,
    )
    assert isinstance(connection.server_info, ServerInfo)
    assert connection.organization_name == ORG_NAME
    assert connection.organization_id == UUID(ORG_ID)


def test_connection_includes_python_version_header(connection: Connection) -> None:
    """Test that Connection object includes Python version in request_headers."""
    expected_python_version = (
        f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
    )

    assert FIDDLER_PYTHON_VERSION_HEADER in connection.request_headers, (
        f'Missing {FIDDLER_PYTHON_VERSION_HEADER} in request_headers'
    )

    actual_python_version = connection.request_headers[FIDDLER_PYTHON_VERSION_HEADER]
    assert actual_python_version == expected_python_version, (
        f'Python version mismatch: expected {expected_python_version}, got {actual_python_version}'
    )


@responses.activate
def test_python_version_header_sent(connection: Connection) -> None:
    """Test that Python version header is included in API requests."""
    expected_python_version = (
        f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
    )

    params = {'client_name': CLIENT_NAME, 'client_version': __version__}
    responses.get(
        url=f'{URL}/v3/version-compatibility',
        match=[
            matchers.query_param_matcher(params),
            matchers.header_matcher(
                {
                    'Authorization': 'Bearer footoken',
                    'X-Fiddler-Client-Name': 'python-sdk',
                    'X-Fiddler-Client-Version': __version__,
                    'X-Fiddler-Python-Version': expected_python_version,
                }
            ),
        ],
    )

    connection._check_version_compatibility()
