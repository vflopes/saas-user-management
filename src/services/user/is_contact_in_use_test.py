import unittest
from unittest.mock import MagicMock

from src.services.user.is_contact_in_use import is_contact_in_use


class IsContactInUseTests(unittest.TestCase):
    def test_returns_true_when_verified_user_found(self):
        client = MagicMock()
        client.list_users.side_effect = [
            {
                "Users": [
                    {
                        "Attributes": [
                            {"Name": "email_verified", "Value": "true"}
                        ]
                    }
                ]
            }
        ]

        result = is_contact_in_use(
            cognito_client=client,
            user_pool_id="pool",
            attribute_name="email",
            attribute_value="user@example.com",
        )

        self.assertTrue(result)
        client.list_users.assert_called_once()

    def test_returns_false_after_pagination_with_no_verified_users(self):
        client = MagicMock()
        client.list_users.side_effect = [
            {
                "Users": [
                    {
                        "Attributes": [
                            {"Name": "email_verified", "Value": "false"}
                        ]
                    }
                ],
                "PaginationToken": "next",
            },
            {"Users": []},
        ]

        result = is_contact_in_use(
            cognito_client=client,
            user_pool_id="pool",
            attribute_name="email",
            attribute_value="user@example.com",
        )

        self.assertFalse(result)
        self.assertEqual(client.list_users.call_count, 2)

    def test_returns_false_when_no_attribute_value(self):
        client = MagicMock()
        result = is_contact_in_use(
            cognito_client=client,
            user_pool_id="pool",
            attribute_name="email",
            attribute_value=None,
        )
        self.assertFalse(result)
        client.list_users.assert_not_called()


if __name__ == "__main__":
    unittest.main()
