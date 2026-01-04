from datetime import datetime, timezone

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_dynamodb import DynamoDBClient

from saas_python_lib.recaptcha import verify_recaptcha

from src.settings import Settings
from src.validators import (
    validate_recaptcha,
    enforce_user_contact_uniqueness,
    validate_user_username,
)
from src.dto.sign_up import PreSignUpValidationData
from src.services.user import is_contact_in_use, register_unverified_user


def process_pre_sign_up(
    event: PreSignUpTriggerEvent,
    settings: Settings,
    cognito_client: CognitoIdentityProviderClient,
    dynamodb_client: DynamoDBClient,
) -> PreSignUpTriggerEvent:
    now = datetime.now(timezone.utc)

    # recaptcha_settings = settings.ensure_recaptcha_settings()
    users_table_settings = settings.ensure_users_table_settings()

    validate_user_username(event.user_name)

    # validation_data = PreSignUpValidationData.load_from_dict(
    #     event.request.validation_data
    # )

    # print("Validating reCAPTCHA token...")
    # print(f"reCAPTCHA token: {validation_data.recaptcha_token}")
    # print(f"Secret key size: {len(recaptcha_settings.secret_key)} characters")
    # validate_recaptcha(
    #     validation_data.recaptcha_token,
    #     recaptcha_settings.secret_key,
    #     verify_recaptcha,
    # )

    # def contact_uniqueness_validator(attribute_name, attribute_value) -> bool:
    #     return is_contact_in_use(
    #         cognito_client=cognito_client,
    #         user_pool_id=event.user_pool_id,
    #         attribute_name=attribute_name,
    #         attribute_value=attribute_value,
    #     )

    # enforce_user_contact_uniqueness(event, contact_uniqueness_validator)

    register_unverified_user(event, users_table_settings, dynamodb_client, now)

    for attr in ("auto_confirm_user", "auto_verify_email", "auto_verify_phone"):
        setattr(event.response, attr, False)

    return event
