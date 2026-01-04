"""
version: 1.0.0
"""

from src.settings import Settings
import src.adapters.aws as aws_adapter

from datetime import datetime, timezone

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PostConfirmationTriggerEvent,
)

from src.services.user import set_user_as_verified

settings = Settings.model_validate({})
users_table_settings = settings.ensure_users_table_settings()
dynamodb_client = aws_adapter.get_dynamodb_client()


@event_source(data_class=PostConfirmationTriggerEvent)
def lambda_handler(event: PostConfirmationTriggerEvent, context):
    now = datetime.now(timezone.utc)

    set_user_as_verified(
        dynamodb_client, users_table_settings.name, event.user_name, now
    )
