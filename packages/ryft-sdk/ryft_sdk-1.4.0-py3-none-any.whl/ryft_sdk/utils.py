from __future__ import annotations


def determine_base_url(secret_key: str) -> str:
    """
    Determine the base URL based on the secret key pattern.

    Args:
        secret_key: The Ryft API secret key

    Returns:
        The appropriate base URL for the API
    """
    if secret_key.startswith("sk_sandbox"):
        return "https://sandbox-api.ryftpay.com/v1"
    elif secret_key.startswith("sk_"):
        return "https://api.ryftpay.com/v1"
    else:
        raise ValueError("Invalid secret key: expected prefix 'sk_'")
