"""
version: 1.0.0
"""

import src.adapters.aws as aws_adapter

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)

from src.settings import Settings
from src.facades import handle_bus_event


@event_source(data_class=EventBridgeEvent)
def lambda_handler(event: EventBridgeEvent, context):
    settings = Settings.model_validate({})
    cognito_client = aws_adapter.get_cognito_client()

    handle_bus_event(event, settings, cognito_client)

    return {"status": "ok"}
