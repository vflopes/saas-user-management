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
    def _make_event(self, token="token123") -> PreSignUpTriggerEvent:
        return PreSignUpTriggerEvent(
            {
                "request": {"validationData": {"reCaptchaToken": token}},
                "response": {},
            }
        )

    def _make_settings_provider(self, secret="secret"):
        settings = Mock()
        settings.recaptcha.secret_key = secret
        return Mock(return_value=settings)

    def test_parse_validation_data_success(self):
        data = parse_validation_data({"reCaptchaToken": "token123"})
        self.assertEqual(data.recaptcha_token, "token123")

    def test_parse_validation_data_missing_token_raises(self):
        with self.assertRaises(ValueError):
            parse_validation_data({})

    def test_process_pre_signup_success(self):
        event_mock = self._make_event()
        settings_provider = self._make_settings_provider()
        recaptcha_verify = MagicMock(return_value=True)

        result = process_pre_signup(
            event_mock, settings_provider, recaptcha_verify
        )

        self.assertIs(result, event_mock)
        self.assertFalse(event_mock.response.auto_confirm_user)
        self.assertFalse(event_mock.response.auto_verify_email)
        self.assertFalse(event_mock.response.auto_verify_phone)
        recaptcha_verify.assert_called_once_with(
            token="token123", secret_key="secret"
        )

    def test_process_pre_signup_missing_secret_raises(self):
        event_mock = self._make_event()
        settings_provider = self._make_settings_provider(secret="")
        recaptcha_verify = MagicMock(return_value=True)

        with self.assertRaises(ValueError):
            process_pre_signup(event_mock, settings_provider, recaptcha_verify)

    def test_process_pre_signup_recaptcha_fails(self):
        event_mock = self._make_event()
        settings_provider = self._make_settings_provider()
        recaptcha_verify = MagicMock(return_value=False)

        with self.assertRaises(ValueError):
            process_pre_signup(event_mock, settings_provider, recaptcha_verify)

    def test_process_pre_signup_missing_recaptcha_token_raises_and_skips_verify(
        self,
    ):
        event_mock = self._make_event(token="")
        settings_provider = self._make_settings_provider()
        recaptcha_verify = MagicMock()

        with self.assertRaises(ValueError):
            process_pre_signup(event_mock, settings_provider, recaptcha_verify)

        recaptcha_verify.assert_not_called()

    @patch("src.cognito.pre_sign_up_trigger.get_settings")
    @patch(
        "src.cognito.pre_sign_up_trigger.verify_recaptcha", return_value=True
    )
    def test_lambda_handler_enforces_recaptcha_validation(
        self, verify_recaptcha_mock, get_settings_mock
    ):
        settings_provider = self._make_settings_provider()
        get_settings_mock.return_value = settings_provider

        event = self._make_event()
        lambda_handler(event, context=None)

        verify_recaptcha_mock.assert_called_once_with(
            token="token123", secret_key="secret"
        )

    @patch("src.cognito.pre_sign_up_trigger.get_settings")
    @patch(
        "src.cognito.pre_sign_up_trigger.verify_recaptcha", return_value=False
    )
    def test_lambda_handler_recaptcha_failure_raises(
        self, verify_recaptcha_mock, get_settings_mock
    ):
        settings_provider = self._make_settings_provider()
        get_settings_mock.return_value = settings_provider

        event = self._make_event()

        with self.assertRaises(ValueError):
            lambda_handler(event, context=None)

        verify_recaptcha_mock.assert_called_once_with(
            token="token123", secret_key="secret"
        )


if __name__ == "__main__":
    unittest.main()
