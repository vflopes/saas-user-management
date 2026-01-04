import unittest
from unittest.mock import MagicMock

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

from src.validators.enforce_user_contact_uniqueness import (
    enforce_user_contact_uniqueness,
    CONTACT_IN_USE_MESSAGE,
)


class EnforceUserContactUniquenessTests(unittest.TestCase):
    def _event(self, email="user@example.com", phone="+15555550123"):
        return PreSignUpTriggerEvent(
            {
                "userPoolId": "pool",
                "request": {
                    "userAttributes": {"email": email, "phone_number": phone}
                },
                "response": {},
            }
        )

    def test_allows_when_validator_asserts_is_not_in_use(self):
        validator = MagicMock()
        validator.return_value = False

        event = self._event()
        enforce_user_contact_uniqueness(event, validator)

        validator.assert_any_call("email", "user@example.com")
        validator.assert_any_call("phone_number", "+15555550123")

    def test_raises_when_contact_in_use(self):
        validator = MagicMock()
        validator.return_value = True

        event = self._event()
        with self.assertRaisesRegex(ValueError, CONTACT_IN_USE_MESSAGE):
            enforce_user_contact_uniqueness(event, validator)

    def test_ignores_missing_contacts(self):
        validator = MagicMock()
        validator.return_value = True

        event = self._event(email="", phone="")
        enforce_user_contact_uniqueness(event, validator)


if __name__ == "__main__":
    unittest.main()
