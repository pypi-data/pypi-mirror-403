"""Webhook Module."""

import hmac
from datetime import datetime, timezone
from hashlib import sha256


class WebhookSignatureVerificationError(ValueError):
    """Error raised when webhook signature verification fails."""

    pass


class WebhookNoTimestampError(WebhookSignatureVerificationError):
    """Error raised when the timestamp is missing from the signature."""

    def __init__(self) -> None:
        """Initialize WebhookNoTimestampError."""
        super().__init__("No timestamp found")


class WebhookNoSignatureError(WebhookSignatureVerificationError):
    """Error raised when a signature matching the scheme is missing."""

    def __init__(self) -> None:
        """Initialize WebhookNoSignatureError."""
        super().__init__("No signatures found")


class WebhookSignatureMismatchError(WebhookSignatureVerificationError):
    """Error raised when the signature does not match the expected one."""

    def __init__(self) -> None:
        """Initialize WebhookSignatureMismatchError."""
        super().__init__("No signatures found matching the expected signature")


class WebhookTimestampOutsideToleranceError(WebhookSignatureVerificationError):
    """Error raised when timestamp is outside the tolerance window."""

    def __init__(self) -> None:
        """Initialize WebhookTimestampOutsideToleranceError."""
        super().__init__("Timestamp outside the tolerance window")


def verify(
    payload: bytes,
    signature: str,
    secret: str,
    tolerance: int = 300,
    scheme: str = "v1",
) -> None:
    """Verify webhook signature.

    Args:
        payload: Raw webhook request body.
        signature: The signature to verify.
        secret: The webhook secret.
        tolerance: Maximum allowed age of the timestamp in seconds. Defaults to 300.
        scheme: Key for signatures in the signature. Defaults to "v1".

    Raises:
        WebhookNoTimestampError: Error raised when the timestamp is missing from the
            signature.
        WebhookNoSignatureError: Error raised when a signature matching the scheme is
            missing.
        WebhookSignatureMismatchError: Error raised when the signature does not match
            the expected one.
        WebhookTimestampOutsideToleranceError: Error raised when timestamp is outside
            the tolerance window.
    """
    timestamp, signature = _parse_signature(signature, scheme)

    _verify_timestamp(timestamp, tolerance)

    signed_payload = b"%d." % timestamp + payload

    expected_signature = _compute_signature(signed_payload, secret)

    _compare(expected_signature, signature)


def _parse_signature(signature: str, scheme: str) -> tuple[int, str]:
    """Parse the signature to extract timestamp and signature for the schema.

    Args:
        signature: The signature to parse.
        scheme: Key for signatures in the signature.

    Returns:
        Tuple containing timestamp and signature.

    Raises:
        WebhookNoTimestampError: Error raised when the timestamp is missing from the
            signature.
        WebhookNoSignatureError: Error raised when a signature matching the scheme is
            missing.
    """
    list_items = [item.split("=", 1) for item in signature.split(",")]

    timestamp_str = next(
        (item[1] for item in list_items if len(item) == 2 and item[0] == "t"),
        None,
    )
    if timestamp_str is None:
        raise WebhookNoTimestampError()

    matchedSignature = next(
        (item[1] for item in list_items if len(item) == 2 and item[0] == scheme), None
    )

    if not matchedSignature:
        raise WebhookNoSignatureError()

    return int(timestamp_str), matchedSignature


def _compute_signature(payload: bytes, secret: str) -> str:
    """Compute signature using payload and webhook secret.

    Args:
        payload: Payload bytes from the webhook request body.
        secret: The webhook secret.

    Returns:
        Computed signature.
    """
    mac = hmac.new(secret.encode("utf-8"), msg=payload, digestmod=sha256)
    return mac.hexdigest()


def _compare(expected_signature: str, signature: str) -> None:
    """Compare signature with the expected signature.

    Args:
        expected_signature: The expected signature.
        signature: The signature.

    Raises:
        WebhookSignatureMismatchError: Error raised when the signature does not match
            the expected one.
    """
    if hmac.compare_digest(expected_signature, signature):
        return None
    raise WebhookSignatureMismatchError()


def _verify_timestamp(timestamp: int, tolerance: int) -> None:
    """Verify that the webhook timestamp is within the tolerance window.

    Args:
        timestamp: Timestamp from the webhook signature.
        tolerance: Maximum allowed age of the timestamp in seconds.

    Raises:
        WebhookTimestampOutsideToleranceError: Error raised when timestamp is outside
            the tolerance window.
    """
    now_utc = datetime.now(timezone.utc).timestamp()
    if timestamp < now_utc - tolerance or timestamp > now_utc + tolerance:
        raise WebhookTimestampOutsideToleranceError()
