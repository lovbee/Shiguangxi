"""验证 Python 只接受 Gateway/Java 门面写入的身份头。"""

import pytest
from fastapi import HTTPException

from app.core.gateway_identity import (
    GATEWAY_USER_ID_HEADER,
    parse_gateway_user_id,
    user_id_from_gateway_headers,
)


@pytest.mark.parametrize("value", ["1", "42", "999999999"])
def test_gateway_user_id_accepts_positive_integer(value: str):
    assert parse_gateway_user_id(value) == int(value)


@pytest.mark.parametrize("value", [None, "", "0", "-1", " 1", "1 ", "01", "1.0", "abc"])
def test_gateway_user_id_rejects_missing_or_noncanonical_values(value: str | None):
    with pytest.raises(HTTPException) as exc_info:
        parse_gateway_user_id(value)

    assert exc_info.value.status_code == 401


def test_gateway_user_id_reads_standard_header_name_case_insensitively():
    headers = {GATEWAY_USER_ID_HEADER.lower(): "7"}

    # Starlette's Headers is case-insensitive; the route receives that type at runtime.
    from starlette.datastructures import Headers

    assert user_id_from_gateway_headers(Headers(headers=headers)) == 7
