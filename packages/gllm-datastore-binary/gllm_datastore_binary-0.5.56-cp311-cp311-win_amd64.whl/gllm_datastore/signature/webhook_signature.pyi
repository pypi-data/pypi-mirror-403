def generate_webhook_signature_with_timestamp(payload: str | bytes, secret: str, timestamp: str) -> str:
    """Generate HMAC SHA-256 signature with timestamp for webhook payload.

    This function creates a signature that includes a timestamp, which helps prevent
    replay attacks. The timestamp is prepended to the payload before signing.

    Args:
        payload (str | bytes): The webhook payload to sign.
        secret (str): The shared secret key used for signing.
        timestamp (str): Unix timestamp (in seconds) as a string.

    Returns:
        str: The hexadecimal representation of the HMAC SHA-256 signature.
    """
def verify_webhook_signature_with_timestamp(payload: str | bytes, secret: str, received_signature: str, timestamp: str, tolerance_seconds: int = 300) -> bool:
    """Verify HMAC SHA-256 signature with timestamp for webhook payload.

    This function verifies the signature and checks that the timestamp is within
    the acceptable tolerance window. This prevents replay attacks where an attacker
    could intercept and resend old webhook requests.

    Args:
        payload (str | bytes): The webhook payload to verify.
        secret (str): The shared secret key used for verification.
        received_signature (str): The signature received in the webhook request.
        timestamp (str): The timestamp received in the webhook request.
        tolerance_seconds (int): Maximum age of the webhook in seconds. Defaults to 300 (5 minutes).

    Returns:
        bool: True if the signature is valid and timestamp is within tolerance, False otherwise.
    """
