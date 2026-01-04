import uuid


class InvalidUserNameError(ValueError):
    def __init__(self):
        super().__init__("Username must be a valid UUID string")


def validate_user_username(username: str):
    try:
        username_uuid = uuid.UUID(username)
    except ValueError:
        raise InvalidUserNameError() from None
    if username_uuid.version != 4:
        raise InvalidUserNameError()
