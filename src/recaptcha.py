from requests import post


def verify_recaptcha(token: str, secret_key: str) -> bool:
    """Verify reCAPTCHA token with Google's API."""
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {"secret": secret_key, "response": token}
    response = post(url, data=payload)
    response.raise_for_status()
    result = response.json()
    return result.get("success", False)
