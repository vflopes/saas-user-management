from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.settings import CleanUpSettings
from src.cognito.types import (
    CleanUpUnverifiedUserResult,
    ListUnverifiedUsersResult,
    UnverifiedUserTypeDef,
)
import src.cognito.aws_commons as aws_commons

from botocore.exceptions import BotoCoreError, ClientError

from mypy_boto3_cognito_idp.type_defs import UserTypeTypeDef

from aws_lambda_powertools import Logger

logger = Logger()


def _to_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _should_delete_user(
    user: UserTypeTypeDef, grace_period_hours: int, now: datetime
) -> bool:
    if user.get("UserStatus") != "UNCONFIRMED":
        return False

    username = user.get("Username")
    if not username:
        return False

    created_at: Optional[datetime] = user.get("UserCreateDate")
    if not created_at:
        return False

    created_at = _to_aware(created_at)
    if now - created_at < timedelta(hours=grace_period_hours):
        return False

    email_verified = (
        aws_commons.is_attributed_verified(user, "email_verified") == "true"
    )
    phone_verified = aws_commons.is_attributed_verified(
        user, "phone_number_verified"
    )

    return not (email_verified or phone_verified)


def list_unverified_users_handler(
    event: dict,
    cleanup_settings: CleanUpSettings,
    cutoff_deadline: datetime,
) -> ListUnverifiedUsersResult:
    cognito_client_provider = aws_commons.get_cognito_client()

    pagination_token = event.get("next_token")

    params: dict[str, Any] = {
        "UserPoolId": cleanup_settings.user_pool_id,
        "Filter": 'status = "UNCONFIRMED"',
        "Limit": 60,
    }
    if pagination_token:
        params["PaginationToken"] = pagination_token

    client = cognito_client_provider()
    try:
        response = client.list_users(**params)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("Failed to list unverified users") from exc

    users: list[UnverifiedUserTypeDef] = []
    for user in response.get("Users", []):
        if not _should_delete_user(
            user, cleanup_settings.grace_period_hours, cutoff_deadline
        ):
            continue

        username = user.get("Username")
        if not username:
            continue

        user_create_date = user.get("UserCreateDate")
        if not user_create_date:
            continue

        users.append(
            UnverifiedUserTypeDef(
                Username=username,
                UserCreateDate=user_create_date,
            )
        )

    next_token = response.get("PaginationToken")

    return ListUnverifiedUsersResult(users=users, next_token=next_token)


def cleanup_unverified_user_handler(
    event: dict,
    cleanup_settings: CleanUpSettings,
) -> CleanUpUnverifiedUserResult:
    cognito_client_provider = aws_commons.get_cognito_client()
    client = cognito_client_provider()

    user: UnverifiedUserTypeDef = UnverifiedUserTypeDef(**event.get("user", {}))

    try:
        client.admin_delete_user(
            UserPoolId=cleanup_settings.user_pool_id,
            Username=user.username,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("Failed to delete unverified user") from exc

    logger.info("Deleted unverified user", extra={"username": user.username})
    return CleanUpUnverifiedUserResult(
        deleted=True,
        username=user.username,
    )
