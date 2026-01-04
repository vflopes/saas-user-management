"""
version: 1.0.0
"""

from src.settings import Settings
import src.adapters.aws as aws_adapter

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

from src.facades import process_pre_sign_up


@event_source(data_class=PreSignUpTriggerEvent)
def lambda_handler(event: PreSignUpTriggerEvent, context):
    settings = Settings.model_validate({})

    cognito_client = aws_adapter.get_cognito_client()
    dynamodb_client = aws_adapter.get_dynamodb_client()

    processed = process_pre_sign_up(
        event,
        settings,
        cognito_client,
        dynamodb_client,
    )

    return processed.raw_event
