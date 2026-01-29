from unittest.mock import MagicMock

import pytest

from eossr.api.zenodo import http_status


def test_ZenodoHTTPStatus():
    # good status, no error raised

    response = MagicMock(status_code=200)
    status = http_status.ZenodoHTTPStatus(response)
    assert status.code == 200
    assert status.name == "OK"
    assert status.is_error() is False
    status.raise_error()  # does nothing

    # bad status, must raise an HTTPStatusError
    response.status_code = 400
    pytest.raises(
        http_status.HTTPStatusError,
        http_status.ZenodoHTTPStatus,
        response,
    )

    response.status_code = 324123
    # wrong status code, must raise a ValueError
    pytest.raises(
        http_status.HTTPStatusError,
        http_status.ZenodoHTTPStatus,
        response,
    )
