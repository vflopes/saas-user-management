from typing import Callable, Protocol, Annotated

from annotated_types import MinLen

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)
from pydantic import BaseModel, Field, ValidationError

from src.settings import Settings
from saas_python_lib.recaptcha import verify_recaptcha


class RecaptchaVerifier(Protocol):
    def __call__(self, token: str, secret_key: str) -> bool: ...


RecaptchaToken = Annotated[str, MinLen(1)]


class ValidationData(BaseModel):
    recaptcha_token: RecaptchaToken = Field(
        default=...,
        alias="reCaptchaToken",
        description="reCAPTCHA token from client",
    )


def get_settings() -> Callable[[], Settings]:
    settings = Settings.model_validate({})
    return lambda: settings


def parse_validation_data(raw: dict) -> ValidationData:
    try:
        return ValidationData(**(raw or {}))
    except ValidationError as e:
        raise ValueError(f"Invalid validation_data: {e}") from e


def process_pre_signup(
    event: PreSignUpTriggerEvent,
    settings_provider: Callable[[], Settings],
    recaptcha_verify: RecaptchaVerifier,
) -> PreSignUpTriggerEvent:
    recaptcha_secret_key = settings_provider().recaptcha.secret_key
    if not recaptcha_secret_key:
        raise ValueError("reCAPTCHA secret key is not configured")

    validation_data = parse_validation_data(event.request.validation_data)
    is_valid = recaptcha_verify(
        token=validation_data.recaptcha_token,
        secret_key=recaptcha_secret_key,
    )
    if not is_valid:
        raise ValueError("reCAPTCHA verification failed")

    event.response.auto_confirm_user = False
    event.response.auto_verify_email = False
    event.response.auto_verify_phone = False
    return event


@event_source(data_class=PreSignUpTriggerEvent)
def lambda_handler(event: PreSignUpTriggerEvent, context):
    processed = process_pre_signup(
        event=event,
        settings_provider=get_settings(),
        recaptcha_verify=verify_recaptcha,
    )
    return processed.raw_event
