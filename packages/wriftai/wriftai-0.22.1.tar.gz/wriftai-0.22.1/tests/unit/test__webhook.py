import hmac
from datetime import datetime, timezone
from hashlib import sha256
from unittest.mock import patch

import pytest

from wriftai._webhook import (
    WebhookNoSignatureError,
    WebhookNoTimestampError,
    WebhookSignatureMismatchError,
    WebhookTimestampOutsideToleranceError,
    verify,
)


def test_verify_valid_signature() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105
    test_signed_payload = b"%d." % test_timestamp + test_payload

    computed_signature = hmac.new(
        test_secret.encode("utf-8"), msg=test_signed_payload, digestmod=sha256
    ).hexdigest()

    header = f"t={test_timestamp},key2=some-value,key={computed_signature}"

    with patch("wriftai._webhook.datetime") as mock_datetime:
        mock_now = datetime.fromtimestamp(test_timestamp + 200, tz=timezone.utc)
        mock_datetime.now.return_value = mock_now

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
            scheme="key",
        )


@pytest.mark.parametrize("timestamp", [-401, 401])
def test_verify_timestamp_outside_tolerance_raises(timestamp: int) -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105
    test_signed_payload = b"%d." % test_timestamp + test_payload
    computed_signature = hmac.new(
        test_secret.encode("utf-8"), msg=test_signed_payload, digestmod=sha256
    ).hexdigest()

    header = f"t={test_timestamp},v1={computed_signature},v2=some-value"

    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookTimestampOutsideToleranceError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = (
            test_timestamp - timestamp
        )

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
            tolerance=400,
        )
    assert str(exc_info.value) == "Timestamp outside the tolerance window"


def test_verify_no_signature_match_raises() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105

    header = f"t={test_timestamp},v1=signature-2,v2=signature-1"

    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookSignatureMismatchError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = test_timestamp + 200

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
        )
    assert str(exc_info.value) == "No signatures found matching the expected signature"


def test_verify_missing_timestamp_raises() -> None:
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105

    header = "v1=signature-2,v2=signature-1"

    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookNoTimestampError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = 999

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
        )

    assert str(exc_info.value) == "No timestamp found"


def test_verify_missing_signatures_raises() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105

    header = f"t={test_timestamp}"
    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookNoSignatureError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = test_timestamp + 200

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
        )

    assert str(exc_info.value) == "No signatures found"


def test_verify_no_scheme_match_raises() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105
    test_signed_payload = b"%d." % test_timestamp + test_payload
    test_scheme = "v1"

    computed_signature = hmac.new(
        test_secret.encode("utf-8"), msg=test_signed_payload, digestmod=sha256
    ).hexdigest()

    header = f"t={test_timestamp},v2={computed_signature},{test_scheme}=signature-1"

    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookSignatureMismatchError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = test_timestamp + 200

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
            scheme=test_scheme,
        )
    assert str(exc_info.value) == "No signatures found matching the expected signature"


def test_verify_valid_signature_with_spaces_timestamp() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105
    test_signed_payload = b"%d." % test_timestamp + test_payload

    computed_signature = hmac.new(
        test_secret.encode("utf-8"), msg=test_signed_payload, digestmod=sha256
    ).hexdigest()

    header = f" t={test_timestamp},key={computed_signature},key2=some-value"

    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookNoTimestampError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = 999

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
        )

    assert str(exc_info.value) == "No timestamp found"


def test_verify_valid_signature_with_spaces_signatures() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105
    test_signed_payload = b"%d." % test_timestamp + test_payload

    computed_signature = hmac.new(
        test_secret.encode("utf-8"), msg=test_signed_payload, digestmod=sha256
    ).hexdigest()

    header = f"t={test_timestamp}, key={computed_signature},key2=some-value"

    with (
        patch("wriftai._webhook.datetime") as mock_datetime,
        pytest.raises(WebhookNoSignatureError) as exc_info,
    ):
        mock_datetime.now.return_value.timestamp.return_value = test_timestamp + 200

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
        )

    assert str(exc_info.value) == "No signatures found"


def test_first_signature_picked_same_scheme() -> None:
    test_timestamp = 123
    test_payload = b'{"event":"ok"}'
    test_secret = "abcd1234"  # noqa: S105
    test_signed_payload = b"%d." % test_timestamp + test_payload

    computed_signature = hmac.new(
        test_secret.encode("utf-8"), msg=test_signed_payload, digestmod=sha256
    ).hexdigest()

    header = f"t={test_timestamp},key={computed_signature},key=error-prone-signature"

    with patch("wriftai._webhook.datetime") as mock_datetime:
        mock_now = datetime.fromtimestamp(test_timestamp + 200, tz=timezone.utc)
        mock_datetime.now.return_value = mock_now

        verify(
            payload=test_payload,
            signature=header,
            secret=test_secret,
            scheme="key",
        )
