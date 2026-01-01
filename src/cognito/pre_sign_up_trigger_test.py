import unittest
from unittest.mock import MagicMock, Mock, patch

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

from src.cognito.pre_sign_up_trigger import (
    lambda_handler,
    parse_validation_data,
    process_pre_signup,
)


class PreSignUpTriggerTests(unittest.TestCase):
    def _make_event(
        self,
        token="token123",
        email="user@example.com",
        phone="+15555550123",
    ) -> PreSignUpTriggerEvent:
        return PreSignUpTriggerEvent(
            {
                "userPoolId": "user-pool-id",
                "request": {
                    "validationData": {"reCaptchaToken": token},
                    "userAttributes": {
                        "email": email,
                        "phone_number": phone,
                    },
                },
                "response": {},
            }
        )

    def _make_settings(self, secret="secret", include_recaptcha=True):
        settings = Mock()
        if include_recaptcha:
            recaptcha = Mock()
            recaptcha.secret_key = secret
            settings.recaptcha = recaptcha
        else:
            settings.recaptcha = None
        return settings

    def _make_cognito_client(self, responses=None):
        client = Mock()
        client.list_users = MagicMock(
            return_value={"Users": []} if responses is None else responses
        )
        return client

    def test_parse_validation_data_success(self):
        data = parse_validation_data({"reCaptchaToken": "token123"})
        self.assertEqual(data.recaptcha_token, "token123")

    def test_parse_validation_data_missing_token_raises(self):
        with self.assertRaises(ValueError):
            parse_validation_data({})

    def test_process_pre_signup_success(self):
        event_mock = self._make_event()
        settings = self._make_settings()
        recaptcha_verify = MagicMock(return_value=True)
        cognito_client = self._make_cognito_client()

        result = process_pre_signup(
            event_mock,
            settings,
            recaptcha_verify,
            cognito_client_provider=lambda: cognito_client,
        )

        self.assertIs(result, event_mock)
        self.assertFalse(event_mock.response.auto_confirm_user)
        self.assertFalse(event_mock.response.auto_verify_email)
        self.assertFalse(event_mock.response.auto_verify_phone)
        recaptcha_verify.assert_called_once_with(
            token="token123", secret_key="secret"
        )
        cognito_client.list_users.assert_any_call(
            UserPoolId="user-pool-id",
            Filter='email = "user@example.com"',
            Limit=60,
        )
        cognito_client.list_users.assert_any_call(
            UserPoolId="user-pool-id",
            Filter='phone_number = "+15555550123"',
            Limit=60,
        )

    def test_process_pre_signup_missing_secret_raises(self):
        event_mock = self._make_event()
        settings = self._make_settings(include_recaptcha=False)
        recaptcha_verify = MagicMock(return_value=True)
        cognito_client = self._make_cognito_client()

        with self.assertRaises(ValueError):
            process_pre_signup(
                event_mock,
                settings,
                recaptcha_verify,
                cognito_client_provider=lambda: cognito_client,
            )

    def test_process_pre_signup_recaptcha_fails(self):
        event_mock = self._make_event()
        settings = self._make_settings()
        recaptcha_verify = MagicMock(return_value=False)

        with self.assertRaises(ValueError):
            process_pre_signup(
                event_mock,
                settings,
                recaptcha_verify,
                cognito_client_provider=self._make_cognito_client,
            )

    def test_process_pre_signup_missing_recaptcha_token_raises_and_skips_verify(
        self,
    ):
        event_mock = self._make_event(token="")
        settings = self._make_settings()
        recaptcha_verify = MagicMock()
        cognito_client = self._make_cognito_client()

        with self.assertRaises(ValueError):
            process_pre_signup(
                event_mock,
                settings,
                recaptcha_verify,
                cognito_client_provider=lambda: cognito_client,
            )

        recaptcha_verify.assert_not_called()

    def test_process_pre_signup_blocks_when_email_in_use_and_verified(self):
        event_mock = self._make_event()
        settings = self._make_settings()
        recaptcha_verify = MagicMock(return_value=True)
        cognito_client = self._make_cognito_client()
        cognito_client.list_users.side_effect = [
            {
                "Users": [
                    {
                        "Attributes": [
                            {"Name": "email_verified", "Value": "true"},
                        ]
                    }
                ]
            }
        ]

        with self.assertRaises(ValueError):
            process_pre_signup(
                event_mock,
                settings,
                recaptcha_verify,
                cognito_client_provider=lambda: cognito_client,
            )

        cognito_client.list_users.assert_called_once_with(
            UserPoolId="user-pool-id",
            Filter='email = "user@example.com"',
            Limit=60,
        )

    def test_process_pre_signup_allows_when_existing_email_not_verified(self):
        event_mock = self._make_event()
        settings = self._make_settings()
        recaptcha_verify = MagicMock(return_value=True)
        cognito_client = self._make_cognito_client()
        cognito_client.list_users.side_effect = [
            {
                "Users": [
                    {
                        "Attributes": [
                            {"Name": "email_verified", "Value": "false"},
                        ]
                    }
                ]
            },
            {"Users": []},
        ]

        result = process_pre_signup(
            event_mock,
            settings,
            recaptcha_verify,
            cognito_client_provider=lambda: cognito_client,
        )

        self.assertIs(result, event_mock)
        self.assertEqual(cognito_client.list_users.call_count, 2)

    def test_process_pre_signup_blocks_when_phone_in_use_and_verified(self):
        event_mock = self._make_event()
        settings = self._make_settings()
        recaptcha_verify = MagicMock(return_value=True)
        cognito_client = self._make_cognito_client()
        cognito_client.list_users.side_effect = [
            {"Users": []},
            {
                "Users": [
                    {
                        "Attributes": [
                            {"Name": "phone_number_verified", "Value": "true"}
                        ]
                    }
                ]
            },
        ]

        with self.assertRaises(ValueError):
            process_pre_signup(
                event_mock,
                settings,
                recaptcha_verify,
                cognito_client_provider=lambda: cognito_client,
            )

        self.assertEqual(cognito_client.list_users.call_count, 2)

    def test_process_pre_signup_skips_contact_check_when_no_email_or_phone(
        self,
    ):
        event_mock = self._make_event(email="", phone="")
        settings = self._make_settings()
        recaptcha_verify = MagicMock(return_value=True)
        cognito_client = self._make_cognito_client()

        result = process_pre_signup(
            event_mock,
            settings,
            recaptcha_verify,
            cognito_client_provider=lambda: cognito_client,
        )

        self.assertIs(result, event_mock)
        cognito_client.list_users.assert_not_called()

    @patch("src.cognito.pre_sign_up_trigger.Settings.model_validate")
    @patch("src.cognito.pre_sign_up_trigger.aws_commons.get_cognito_client")
    @patch(
        "src.cognito.pre_sign_up_trigger.verify_recaptcha", return_value=True
    )
    def test_lambda_handler_enforces_recaptcha_validation(
        self,
        verify_recaptcha_mock,
        get_cognito_client_mock,
        model_validate_mock,
    ):
        settings = self._make_settings()
        model_validate_mock.return_value = settings
        cognito_client = self._make_cognito_client()
        get_cognito_client_mock.return_value = lambda: cognito_client

        event = self._make_event()
        lambda_handler(event, context=None)

        verify_recaptcha_mock.assert_called_once_with(
            token="token123", secret_key="secret"
        )
        self.assertGreaterEqual(cognito_client.list_users.call_count, 1)

    @patch("src.cognito.pre_sign_up_trigger.Settings.model_validate")
    @patch("src.cognito.pre_sign_up_trigger.aws_commons.get_cognito_client")
    @patch(
        "src.cognito.pre_sign_up_trigger.verify_recaptcha", return_value=False
    )
    def test_lambda_handler_recaptcha_failure_raises(
        self,
        verify_recaptcha_mock,
        get_cognito_client_mock,
        model_validate_mock,
    ):
        settings = self._make_settings()
        model_validate_mock.return_value = settings
        cognito_client = self._make_cognito_client()
        get_cognito_client_mock.return_value = lambda: cognito_client

        event = self._make_event()

        with self.assertRaises(ValueError):
            lambda_handler(event, context=None)

        verify_recaptcha_mock.assert_called_once_with(
            token="token123", secret_key="secret"
        )


if __name__ == "__main__":
    unittest.main()
