from typing import Protocol


class ReCaptchaVerifier(Protocol):
    def __call__(self, token: str, secret_key: str) -> bool: ...


class InvalidReCaptchaError(ValueError):
    def __init__(self):
        super().__init__("reCAPTCHA verification failed. please try again.")


def validate_recaptcha(
    recaptcha_token: str,
    secret_key: str,
    recaptcha_verify: ReCaptchaVerifier,
) -> None:
    is_valid = recaptcha_verify(
        token=recaptcha_token,
        secret_key=secret_key,
    )
    if not is_valid:
        raise InvalidReCaptchaError()
