from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)
from pydantic import BaseModel, ValidationError, Field
from typing import Callable

from src.settings import Settings

from src.recaptcha import verify_recaptcha


class ClientMetadata(BaseModel):
    recaptcha_token: str = Field(
        default=...,
        alias="reCaptchaToken",
        description="reCAPTCHA token from client",
    )


def get_settings() -> Callable[[], Settings]:
    settings = Settings.model_validate({})
    return lambda: settings


@event_source(data_class=PreSignUpTriggerEvent)
def lambda_handler(event: PreSignUpTriggerEvent, context):
    settings = get_settings()

    recaptcha_secret_key = settings().recaptcha.secret_key

    if not recaptcha_secret_key:
        raise ValueError("reCAPTCHA secret key is not configured")

    try:
        # Validate client_metadata
        # client_metadata can be None in the event, so default to {}
        metadata_dict = event.request.client_metadata or {}
        client_metadata = ClientMetadata(**metadata_dict)
    except ValidationError as e:
        # Raise an error to prevent sign up if validation fails
        raise ValueError(f"Invalid client_metadata: {e}") from e

    is_valid = verify_recaptcha(
        token=client_metadata.recaptcha_token,
        secret_key=recaptcha_secret_key,
    )

    if not is_valid:
        raise ValueError("reCAPTCHA verification failed")

    event.response.auto_confirm_user = False
    event.response.auto_verify_email = False
    event.response.auto_verify_phone = False

    return event.raw_event
