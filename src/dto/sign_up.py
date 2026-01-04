from pydantic import BaseModel, Field, ValidationError
from typing import Annotated
from annotated_types import MinLen

RecaptchaToken = Annotated[str, MinLen(1)]


class PreSignUpValidationData(BaseModel):
    recaptcha_token: RecaptchaToken = Field(
        default=...,
        alias="reCaptchaToken",
        description="reCAPTCHA token from client",
    )

    @staticmethod
    def load_from_dict(raw: dict) -> "PreSignUpValidationData":
        try:
            return PreSignUpValidationData(**(raw or {}))
        except ValidationError as e:
            raise ValueError(f"Invalid validation_data: {e}") from e
