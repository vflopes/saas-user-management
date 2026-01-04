import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.services.user.set_user_as_verified import set_user_as_verified


class SetUserAsVerifiedTests(unittest.TestCase):
    def test_updates_with_epoch_and_removes_ttl(self):
        dynamodb = MagicMock()
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)

        set_user_as_verified(
            dynamodb_client=dynamodb,
            user_table_name="users-table",
            user_id="user-123",
            now=now,
        )

        dynamodb.update_item.assert_called_once()
        args, kwargs = dynamodb.update_item.call_args
        self.assertEqual(kwargs["Key"], {"user_id": {"S": "user-123"}})
        self.assertEqual(
            kwargs["ExpressionAttributeValues"],
            {":verified_at": {"N": str(int(now.timestamp()))}},
        )
        self.assertIn("REMOVE expires_at", kwargs["UpdateExpression"])


if __name__ == "__main__":
    unittest.main()
