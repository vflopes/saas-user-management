from typing import Protocol

from aws_lambda_powertools.utilities.data_classes.cognito_user_pool_event import (
    PreSignUpTriggerEvent,
)

CONTACT_IN_USE_MESSAGE = (
    "We can't create an account with this contact information. "
    "Please sign in or recover your account instead."
)


class ContactInUseError(ValueError):
    def __init__(self):
        super().__init__(CONTACT_IN_USE_MESSAGE)


class ContactValidator(Protocol):
    def __call__(self, attribute_name: str, attribute_value: str) -> bool: ...


def enforce_user_contact_uniqueness(
    event: PreSignUpTriggerEvent,
    contact_validator: ContactValidator,
) -> None:
    user_attributes = event.request.user_attributes or {}

    contact_checks = (
        (
            "email",
            user_attributes.get("email"),
        ),
        (
            "phone_number",
            user_attributes.get("phone_number"),
        ),
    )

    for (
        attribute_name,
        attribute_value,
    ) in contact_checks:
        if not attribute_value:
            continue
        if contact_validator(
            attribute_name,
            attribute_value,
        ):
            raise ContactInUseError()
