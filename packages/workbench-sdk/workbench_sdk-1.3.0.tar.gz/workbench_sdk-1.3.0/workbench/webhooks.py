"""
Webhook signature verification utilities.

Workbench signs all webhook payloads using HMAC-SHA256. This module provides
utilities to verify these signatures to ensure webhook authenticity.
"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Tuple, Union


class WebhookVerificationError(Exception):
    """Error raised when webhook signature verification fails."""

    pass


def parse_signature_header(header: str) -> Tuple[int, str]:
    """
    Parse the X-Workbench-Signature header value.

    The header format is: t=<timestamp>,v1=<signature>

    Args:
        header: The X-Workbench-Signature header value

    Returns:
        Tuple of (timestamp, signature)

    Raises:
        WebhookVerificationError: If the header format is invalid

    Example:
        >>> timestamp, signature = parse_signature_header(
        ...     "t=1706400000,v1=5257a869e..."
        ... )
    """
    if not header or not isinstance(header, str):
        raise WebhookVerificationError("Missing or invalid signature header")

    timestamp: Optional[int] = None
    signature: Optional[str] = None

    for part in header.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                raise WebhookVerificationError("Invalid timestamp in signature header")
        elif key == "v1":
            signature = value

    if timestamp is None or signature is None:
        raise WebhookVerificationError("Invalid signature header format")

    return timestamp, signature


def compute_signature(payload: Union[str, bytes], secret: str, timestamp: int) -> str:
    """
    Compute the expected signature for a webhook payload.

    Args:
        payload: The raw webhook payload (string or bytes)
        secret: The webhook secret
        timestamp: The timestamp from the signature header

    Returns:
        The expected HMAC-SHA256 signature

    Example:
        >>> expected = compute_signature(
        ...     '{"event":"client.created",...}',
        ...     "whsec_xxx",
        ...     1706400000
        ... )
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return signature


def verify_webhook_signature(
    payload: Union[str, bytes],
    signature: str,
    secret: str,
    tolerance: int = 300,
) -> bool:
    """
    Verify a Workbench webhook signature.

    This function verifies that a webhook payload was sent by Workbench and
    hasn't been tampered with. It also checks that the webhook isn't too old
    to prevent replay attacks.

    Args:
        payload: The raw webhook payload (string or bytes)
        signature: The X-Workbench-Signature header value
        secret: Your webhook secret (starts with whsec_)
        tolerance: Maximum age of the webhook in seconds (default: 300 = 5 minutes)
                  Set to 0 to disable timestamp validation

    Returns:
        True if the signature is valid

    Raises:
        WebhookVerificationError: If verification fails

    Example:
        >>> from workbench import verify_webhook_signature
        >>>
        >>> # In your webhook handler
        >>> payload = request.body
        >>> signature = request.headers["X-Workbench-Signature"]
        >>> secret = os.environ["WEBHOOK_SECRET"]
        >>>
        >>> try:
        ...     verify_webhook_signature(payload, signature, secret)
        ...     event = json.loads(payload)
        ...     print(f"Received event: {event['event']}")
        ... except WebhookVerificationError as e:
        ...     print(f"Verification failed: {e}")
    """
    # Parse the signature header
    timestamp, provided_signature = parse_signature_header(signature)

    # Check timestamp tolerance (prevent replay attacks)
    if tolerance > 0:
        now = int(time.time())
        age = now - timestamp

        if age > tolerance:
            raise WebhookVerificationError(
                f"Webhook timestamp is too old ({age} seconds). "
                f"Maximum allowed age is {tolerance} seconds."
            )

        if age < -tolerance:
            raise WebhookVerificationError(
                "Webhook timestamp is in the future. Check your server clock."
            )

    # Compute the expected signature
    expected_signature = compute_signature(payload, secret, timestamp)

    # Use timing-safe comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise WebhookVerificationError("Invalid webhook signature")

    return True


def construct_webhook_event(
    payload: Union[str, bytes],
    signature: str,
    secret: str,
    tolerance: int = 300,
) -> Dict[str, Any]:
    """
    Construct a webhook event from a verified payload.

    This is a convenience function that verifies the signature and parses
    the payload in one step.

    Args:
        payload: The raw webhook payload (string or bytes)
        signature: The X-Workbench-Signature header value
        secret: Your webhook secret
        tolerance: Maximum age of the webhook in seconds (default: 300)

    Returns:
        The parsed webhook event

    Raises:
        WebhookVerificationError: If verification fails

    Example:
        >>> from workbench import construct_webhook_event
        >>>
        >>> event = construct_webhook_event(payload, signature, secret)
        >>> print(f"Event type: {event['event']}")
        >>> print(f"Event data: {event['data']}")
    """
    verify_webhook_signature(payload, signature, secret, tolerance)

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        raise WebhookVerificationError("Invalid webhook payload: not valid JSON")
