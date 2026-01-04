import unittest
from unittest.mock import MagicMock

from src.validators.validate_recaptcha import validate_recaptcha


class ValidateRecaptchaTests(unittest.TestCase):
    def test_validate_recaptcha_success(self):
        verifier = MagicMock(return_value=True)
        validate_recaptcha("token", "secret", verifier)
        verifier.assert_called_once_with(token="token", secret_key="secret")

    def test_validate_recaptcha_failure_raises(self):
        verifier = MagicMock(return_value=False)
        with self.assertRaises(ValueError):
            validate_recaptcha("token", "secret", verifier)
        verifier.assert_called_once()


if __name__ == "__main__":
    unittest.main()
