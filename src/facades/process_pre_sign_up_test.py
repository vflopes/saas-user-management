import unittest
from unittest.mock import MagicMock, patch

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)


from src.validators.validate_user_username import InvalidUserNameError
from src.validators.validate_recaptcha import InvalidReCaptchaError
from src.validators.enforce_user_contact_uniqueness import ContactInUseError

from .process_pre_sign_up import process_pre_sign_up


class ProcessPreSignUpTests(unittest.TestCase):
    def _event(self, username="0fcbc418-e084-478c-9af0-fa616f1761f0"):
        return PreSignUpTriggerEvent(
            {
                "userPoolId": "pool-id",
                "userName": username,
                "request": {
                    "validationData": {"reCaptchaToken": "token"},
                    "userAttributes": {
                        "sub": "user-123",
                        "email": "user@example.com",
                        "phone_number": "+15555550123",
                    },
                },
                "response": {},
            }
        )

    def _settings(self):
        recaptcha_settings = MagicMock()
        recaptcha_settings.secret_key = "secret-key"

        users_table_settings = MagicMock()
        users_table_settings.name = "users-table"
        users_table_settings.expire_unverified_users_minutes = 15

        settings = MagicMock()
        settings.ensure_recaptcha_settings.return_value = recaptcha_settings
        settings.ensure_users_table_settings.return_value = users_table_settings

        return settings

    def test_validate_invalid_username(self):
        event = self._event(username="bad-username")
        settings = self._settings()

        with self.assertRaises(InvalidUserNameError):
            process_pre_sign_up(event, settings, MagicMock(), MagicMock())

    @patch("facades.process_pre_sign_up.validate_recaptcha")
    def test_validate_recaptcha_failure(self, mock_validate_recaptcha):
        event = self._event()
        settings = self._settings()

        mock_validate_recaptcha.side_effect = InvalidReCaptchaError()

        with self.assertRaises(InvalidReCaptchaError):
            process_pre_sign_up(event, settings, MagicMock(), MagicMock())

        mock_validate_recaptcha.assert_called_once()

    @patch("facades.process_pre_sign_up.validate_recaptcha")
    @patch("facades.process_pre_sign_up.is_contact_in_use")
    def test_contact_in_use_raises(
        self, mock_is_contact_in_use, mock_validate_recaptcha
    ):
        event = self._event()
        settings = self._settings()

        mock_is_contact_in_use.return_value = True

        with self.assertRaises(ContactInUseError):
            process_pre_sign_up(event, settings, MagicMock(), MagicMock())

        mock_validate_recaptcha.assert_called_once()

    @patch("facades.process_pre_sign_up.validate_recaptcha")
    @patch("facades.process_pre_sign_up.is_contact_in_use")
    @patch("facades.process_pre_sign_up.enforce_user_contact_uniqueness")
    def test_enforce_user_contact_uniqueness_raises(
        self,
        mock_enforce_user_contact_uniqueness,
        mock_is_contact_in_use,
        mock_validate_recaptcha,
    ):
        event = self._event()
        settings = self._settings()

        mock_enforce_user_contact_uniqueness.side_effect = ContactInUseError()

        with self.assertRaises(ContactInUseError):
            process_pre_sign_up(event, settings, MagicMock(), MagicMock())

        mock_is_contact_in_use.assert_not_called()
        mock_validate_recaptcha.assert_called_once()

    @patch("facades.process_pre_sign_up.validate_recaptcha")
    @patch("facades.process_pre_sign_up.is_contact_in_use")
    @patch("facades.process_pre_sign_up.enforce_user_contact_uniqueness")
    @patch("facades.process_pre_sign_up.register_unverified_user")
    def test_enforce_user_contact_uniqueness_called(
        self,
        mock_register_unverified_user,
        mock_enforce_user_contact_uniqueness,
        mock_is_contact_in_use,
        mock_validate_recaptcha,
    ):
        event = self._event()
        settings = self._settings()

        process_pre_sign_up(event, settings, MagicMock(), MagicMock())

        mock_validate_recaptcha.assert_called_once()
        mock_is_contact_in_use.assert_not_called()
        mock_enforce_user_contact_uniqueness.assert_called_once()
        mock_register_unverified_user.assert_called_once()


if __name__ == "__main__":
    unittest.main()
