import unittest
from unittest.mock import MagicMock, Mock

from src.cognito.pre_sign_up_trigger import (
    parse_validation_data,
    process_pre_signup,
)


class PreSignUpTriggerTests(unittest.TestCase):
    def test_parse_validation_data_success(self):
        data = parse_validation_data({"reCaptchaToken": "token123"})
        self.assertEqual(data.recaptcha_token, "token123")

    def test_parse_validation_data_missing_token_raises(self):
        with self.assertRaises(ValueError):
            parse_validation_data({})

    def test_process_pre_signup_success(self):
        event_mock = Mock()
        event_mock.request.validation_data = {"reCaptchaToken": "token123"}
        settings_mock = Mock()
        settings_mock.recaptcha.secret_key = "secret"
        settings_provider = Mock(return_value=settings_mock)
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
        event_mock = Mock()
        event_mock.request.validation_data = {"reCaptchaToken": "token123"}
        settings_mock = Mock()
        settings_mock.recaptcha.secret_key = None
        settings_provider = Mock(return_value=settings_mock)
        recaptcha_verify = MagicMock(return_value=True)

        with self.assertRaises(ValueError):
            process_pre_signup(event_mock, settings_provider, recaptcha_verify)

    def test_process_pre_signup_recaptcha_fails(self):
        event_mock = Mock()
        event_mock.request.validation_data = {"reCaptchaToken": "token123"}
        settings_mock = Mock()
        settings_mock.recaptcha.secret_key = "secret"
        settings_provider = Mock(return_value=settings_mock)
        recaptcha_verify = MagicMock(return_value=False)

        with self.assertRaises(ValueError):
            process_pre_signup(event_mock, settings_provider, recaptcha_verify)


if __name__ == "__main__":
    unittest.main()
