from typing import Any, Optional

from saas_python_lib.settings import (
    get_aws_ssm_parameter_value,
    is_aws_session_token_available,
)

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class ReCaptchaSettings(BaseModel):
    secret_key: Optional[str]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    def model_post_init(self, __context: Any) -> None:
        if not is_aws_session_token_available():
            return

        # Override secret_key with value from AWS SSM
        if self.recaptcha.secret_key is not None:
            self.recaptcha.secret_key = get_aws_ssm_parameter_value(
                parameter_name=self.recaptcha.secret_key,
            )

    recaptcha: ReCaptchaSettings
