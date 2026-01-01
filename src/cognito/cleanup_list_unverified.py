from datetime import datetime, timezone

from src.settings import Settings
from src.cognito.cleanup_unverified_users import (
    list_unverified_users_handler,
)

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(
    event: dict,
    context: LambdaContext,
) -> dict:
    settings = Settings.model_validate({})

    cleanup_settings = settings.cleanup

    if not cleanup_settings:
        raise ValueError("Cleanup settings are not configured")

    result = list_unverified_users_handler(
        event=event,
        cleanup_settings=cleanup_settings,
        cutoff_deadline=datetime.now(timezone.utc),
    )

    return result.model_dump()
