import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from mypy_boto3_cognito_idp.type_defs import UserTypeTypeDef
from mypy_boto3_cognito_idp.literals import UserStatusTypeType


from src.cognito.cleanup_unverified_users import (
    cleanup_unverified_user_handler,
    list_unverified_users_handler,
    _should_delete_user,
)
from src.settings import CleanUpSettings


class CleanupUnverifiedUsersTests(unittest.TestCase):
    def _user(
        self,
        *,
        age_hours: int = 25,
        status: UserStatusTypeType = "UNCONFIRMED",
        email_verified: str = "false",
        phone_verified: str = "false",
    ) -> UserTypeTypeDef:
        created_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
        return {
            "Username": "user-123",
            "UserStatus": status,
            "UserCreateDate": created_at,
            "Attributes": [
                {"Name": "email_verified", "Value": email_verified},
                {"Name": "phone_number_verified", "Value": phone_verified},
            ],
        }

    def _cleanup_settings(self):
        return CleanUpSettings(user_pool_id="pool-123", grace_period_hours=24)

    @patch(
        "src.cognito.cleanup_unverified_users.aws_commons.get_cognito_client"
    )
    def test_cleanup_deletes_stale_unverified_user(self, get_client_mock):
        user = self._user()
        client = MagicMock()
        client.admin_delete_user = MagicMock()
        get_client_mock.return_value = lambda: client

        result = cleanup_unverified_user_handler(
            {"user": user},
            cleanup_settings=self._cleanup_settings(),
        )

        client.admin_delete_user.assert_called_once_with(
            UserPoolId="pool-123", Username="user-123"
        )
        self.assertTrue(result.deleted)
        self.assertEqual("user-123", result.username)

    @patch(
        "src.cognito.cleanup_unverified_users.aws_commons.get_cognito_client"
    )
    def test_cleanup_deletes_when_event_provided(self, get_client_mock):
        user = self._user()
        client = MagicMock()
        get_client_mock.return_value = lambda: client

        result = cleanup_unverified_user_handler(
            {"user": user},
            cleanup_settings=self._cleanup_settings(),
        )

        client.admin_delete_user.assert_called_once_with(
            UserPoolId="pool-123", Username="user-123"
        )
        self.assertTrue(result.deleted)

    def test_should_delete_user_respects_verification_flags(self):
        now = datetime(2024, 1, 2, tzinfo=timezone.utc)
        user = self._user(email_verified="true")
        self.assertFalse(
            _should_delete_user(user, grace_period_hours=1, now=now)
        )

        user = self._user(phone_verified="true")
        self.assertFalse(
            _should_delete_user(user, grace_period_hours=1, now=now)
        )

    def test_should_delete_requires_unconfirmed_status(self):
        now = datetime(2024, 1, 2, tzinfo=timezone.utc)
        user = self._user(status="CONFIRMED")
        self.assertFalse(
            _should_delete_user(user, grace_period_hours=1, now=now)
        )

    @patch(
        "src.cognito.cleanup_unverified_users.aws_commons.get_cognito_client"
    )
    def test_list_unverified_users_returns_expected_shape(
        self, get_client_mock
    ):
        user = self._user()
        client = MagicMock()
        client.list_users.return_value = {
            "Users": [user],
            "PaginationToken": "next-1",
        }
        get_client_mock.return_value = lambda: client

        result = list_unverified_users_handler(
            {"next_token": "token-1"},
            cleanup_settings=self._cleanup_settings(),
            cutoff_deadline=datetime.now(timezone.utc),
        )

        client.list_users.assert_called_once()
        self.assertEqual(1, len(result.users))
        self.assertEqual("next-1", result.next_token)
        listed_user = result.users[0]
        self.assertEqual("user-123", listed_user.username)
        self.assertTrue(listed_user.user_create_date)


if __name__ == "__main__":
    unittest.main()
