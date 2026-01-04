from datetime import datetime, timedelta, timezone

from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_dynamodb import DynamoDBClient

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

from src.settings import UsersTableSettings


def _compute_expiration_ts(minutes: int, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    return int((now + timedelta(minutes=minutes)).timestamp())


def _build_user_record(user_id: str, ttl_minutes: int, now: datetime) -> dict:
    return {
        "user_id": {"S": user_id},
        "created_at": {"N": str(int(now.timestamp()))},
        "expires_at": {"N": str(_compute_expiration_ts(ttl_minutes, now))},
    }


def register_unverified_user(
    event: PreSignUpTriggerEvent,
    users_table_settings: UsersTableSettings,
    dynamodb_client: DynamoDBClient,
    now: datetime,
) -> None:
    user_id = event.request.user_attributes.get("sub") or event.user_name
    if not user_id:
        raise ValueError("User identifier is missing.")

    item = _build_user_record(
        user_id, users_table_settings.expire_unverified_users_minutes, now
    )

    try:
        dynamodb_client.put_item(
            TableName=users_table_settings.name,
            Item=item,
            ConditionExpression="attribute_not_exists(user_id)",
        )
    except (BotoCoreError, ClientError) as exc:
        raise ValueError("Unable to register user record.") from exc
