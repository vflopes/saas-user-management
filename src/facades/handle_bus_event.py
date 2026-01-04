from typing import List

from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import BotoCoreError, ClientError

from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)

from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_dynamodbstreams.type_defs import (
    GetRecordsOutputTypeDef,
)

from src.settings import Settings

deserializer = TypeDeserializer()


def _extract_removed_user_ids(detail: GetRecordsOutputTypeDef) -> List[str]:
    records = filter(
        lambda record: record.get("eventName") == "REMOVE",
        detail.get("Records") or [],
    )
    user_ids: List[str] = []

    for record in records:
        keys = record.get("dynamodb", {}).get("Keys", {})
        user_keys = deserializer.deserialize({"M": keys})  # type: ignore

        user_id = user_keys.get("user_id", None)
        if user_id:
            user_ids.append(user_id)

    return user_ids


def handle_bus_event(
    event: EventBridgeEvent,
    settings: Settings,
    cognito_client: CognitoIdentityProviderClient,
) -> None:
    user_pool_settings = settings.ensure_user_pool_settings()

    user_ids = _extract_removed_user_ids(
        GetRecordsOutputTypeDef(**event.detail or {})
    )
    for user_id in user_ids:
        try:
            cognito_client.admin_delete_user(
                UserPoolId=user_pool_settings.id,
                Username=user_id,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("Failed to delete user from Cognito") from exc
