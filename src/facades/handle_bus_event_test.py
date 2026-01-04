import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from .handle_bus_event import handle_bus_event

from botocore.exceptions import ClientError

from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)


class HandleBusEventTests(unittest.TestCase):
    def _settings(self):
        settings = MagicMock()
        settings.ensure_user_pool_settings.return_value = SimpleNamespace(
            id="user-pool-id"
        )
        return settings

    def test_deletes_all_removed_user_ids(self):
        settings = self._settings()
        cognito_client = MagicMock()
        event = EventBridgeEvent(
            {
                "detail": {
                    "Records": [
                        {
                            "eventName": "REMOVE",
                            "dynamodb": {"Keys": {"user_id": {"S": "user-1"}}},
                        },
                        {
                            "eventName": "MODIFY",
                            "dynamodb": {
                                "Keys": {"user_id": {"S": "user-ignored"}}
                            },
                        },
                        {
                            "eventName": "REMOVE",
                            "dynamodb": {"Keys": {"user_id": {"S": "user-2"}}},
                        },
                    ]
                }
            }
        )

        handle_bus_event(event, settings, cognito_client)

        settings.ensure_user_pool_settings.assert_called_once()
        self.assertEqual(cognito_client.admin_delete_user.call_count, 2)
        cognito_client.admin_delete_user.assert_any_call(
            UserPoolId="user-pool-id", Username="user-1"
        )
        cognito_client.admin_delete_user.assert_any_call(
            UserPoolId="user-pool-id", Username="user-2"
        )

    def test_ignores_events_without_removals(self):
        settings = self._settings()
        cognito_client = MagicMock()
        event = EventBridgeEvent(
            {"detail": {"Records": [{"eventName": "MODIFY", "dynamodb": {}}]}}
        )

        handle_bus_event(event, settings, cognito_client)

        settings.ensure_user_pool_settings.assert_called_once()
        cognito_client.admin_delete_user.assert_not_called()

    def test_raises_when_cognito_delete_fails(self):
        settings = self._settings()
        cognito_client = MagicMock()
        cognito_client.admin_delete_user.side_effect = ClientError(
            {"Error": {"Code": "Error", "Message": "boom"}}, "AdminDeleteUser"
        )
        event = EventBridgeEvent(
            {
                "detail": {
                    "Records": [
                        {
                            "eventName": "REMOVE",
                            "dynamodb": {"Keys": {"user_id": {"S": "user-1"}}},
                        }
                    ]
                }
            }
        )

        with self.assertRaisesRegex(RuntimeError, "Failed to delete user"):
            handle_bus_event(event, settings, cognito_client)


if __name__ == "__main__":
    unittest.main()
