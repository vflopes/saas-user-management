import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

from src.services.user.register_unverified_user import (
    register_unverified_user,
)
from src.settings import UsersTableSettings


class RegisterUnverifiedUserTests(unittest.TestCase):
    def _event(self, username="user-123"):
        return PreSignUpTriggerEvent(
            {
                "userPoolId": "pool",
                "userName": username,
                "request": {
                    "userAttributes": {
                        "sub": "user-123",
                    }
                },
                "response": {},
            }
        )

    def test_registers_user_with_epoch_fields(self):
        dynamodb = MagicMock()
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)

        register_unverified_user(
            event=self._event(),
            users_table_settings=UsersTableSettings(
                name="users-table", expire_unverified_users_minutes=60
            ),
            dynamodb_client=dynamodb,
            now=now,
        )

        args, kwargs = dynamodb.put_item.call_args
        item = kwargs["Item"]
        self.assertEqual(item["user_id"]["S"], "user-123")
        self.assertEqual(item["created_at"]["N"], str(int(now.timestamp())))
        self.assertTrue(item["expires_at"]["N"].isdigit())

    def test_missing_user_id_raises(self):
        event = self._event(username="")
        event.request.user_attributes.pop("sub")
        with self.assertRaises(ValueError):
            register_unverified_user(
                event=event,
                users_table_settings=UsersTableSettings(
                    name="users-table", expire_unverified_users_minutes=60
                ),
                dynamodb_client=MagicMock(),
                now=datetime.now(timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
