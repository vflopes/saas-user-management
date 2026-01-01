from typing import Annotated, Callable, Protocol
from annotated_types import MinLen

from botocore.exceptions import BotoCoreError, ClientError

import src.cognito.aws_commons as aws_commons

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

from pydantic import BaseModel, Field, ValidationError

from src.settings import Settings
from saas_python_lib.recaptcha import verify_recaptcha


class RecaptchaVerifier(Protocol):
    def __call__(self, token: str, secret_key: str) -> bool: ...


RecaptchaToken = Annotated[str, MinLen(1)]

CONTACT_IN_USE_MESSAGE = (
    "We can't create an account with this contact information. "
    "Please sign in or recover your account instead."
)


class ValidationData(BaseModel):
    recaptcha_token: RecaptchaToken = Field(
        default=...,
        alias="reCaptchaToken",
        description="reCAPTCHA token from client",
    )


def parse_validation_data(raw: dict) -> ValidationData:
    try:
        return ValidationData(**(raw or {}))
    except ValidationError as e:
        raise ValueError(f"Invalid validation_data: {e}") from e


def _contact_in_use(
    cognito_client: CognitoIdentityProviderClient,
    user_pool_id: str,
    attribute_name: str,
    verified_attribute_name: str,
    attribute_value: str | None,
) -> bool:
    if not attribute_value:
        return False

    filter_value = attribute_value
    pagination_token: str | None = None

    try:
        while True:
            params = {
                "UserPoolId": user_pool_id,
                "Filter": f'{attribute_name} = "{filter_value}"',
                "Limit": 60,
            }
            if pagination_token:
                params["PaginationToken"] = pagination_token

            response = cognito_client.list_users(**params)
            for user in response.get("Users", []):
                if aws_commons.is_attributed_verified(
                    user, verified_attribute_name
                ):
                    return True

            pagination_token = response.get("PaginationToken")
            if not pagination_token:
                break

    except (BotoCoreError, ClientError) as exc:
        raise ValueError(
            "Unable to validate contact information. Please try again."
        ) from exc

    return False


def enforce_contact_uniqueness(
    event: PreSignUpTriggerEvent,
    cognito_client_provider: Callable[[], CognitoIdentityProviderClient],
) -> None:
    cognito_client = cognito_client_provider()
    user_pool_id = event.user_pool_id
    user_attributes = event.request.user_attributes or {}

    contact_checks = (
        (
            "email",
            "email_verified",
            user_attributes.get("email"),
        ),
        (
            "phone_number",
            "phone_number_verified",
            user_attributes.get("phone_number"),
        ),
    )

    for (
        attribute_name,
        verified_attribute_name,
        attribute_value,
    ) in contact_checks:
        if _contact_in_use(
            cognito_client,
            user_pool_id,
            attribute_name,
            verified_attribute_name,
            attribute_value,
        ):
            raise ValueError(CONTACT_IN_USE_MESSAGE)


def process_pre_signup(
    event: PreSignUpTriggerEvent,
    settings: Settings,
    recaptcha_verify: RecaptchaVerifier,
    cognito_client_provider: Callable[[], CognitoIdentityProviderClient],
) -> PreSignUpTriggerEvent:
    recaptcha_settings = settings.recaptcha
    if not recaptcha_settings:
        raise ValueError("reCAPTCHA secret key is not configured")

    validation_data = parse_validation_data(event.request.validation_data)
    is_valid = recaptcha_verify(
        token=validation_data.recaptcha_token,
        secret_key=recaptcha_settings.secret_key,
    )
    if not is_valid:
        raise ValueError("reCAPTCHA verification failed")

    enforce_contact_uniqueness(event, cognito_client_provider)

    event.response.auto_confirm_user = False
    event.response.auto_verify_email = False
    event.response.auto_verify_phone = False
    return event


@event_source(data_class=PreSignUpTriggerEvent)
def lambda_handler(event: PreSignUpTriggerEvent, context):
    processed = process_pre_signup(
        event=event,
        settings=Settings.model_validate({}),
        recaptcha_verify=verify_recaptcha,
        cognito_client_provider=aws_commons.get_cognito_client(),
    )
    return processed.raw_event
