import unittest
import uuid

from src.validators.validate_user_username import validate_user_username


class ValidateUserUsernameTests(unittest.TestCase):
    def test_accepts_valid_uuid_string(self):
        username = str(uuid.uuid4())

        validate_user_username(username)

    def test_raises_for_invalid_uuid_string(self):
        with self.assertRaisesRegex(
            ValueError, "Username must be a valid UUID string"
        ):
            validate_user_username("not-a-uuid")


if __name__ == "__main__":
    unittest.main()
