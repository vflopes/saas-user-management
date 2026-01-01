from typing import Any, Optional, Annotated
from annotated_types import Ge

from saas_python_lib.settings import (
    get_required_aws_ssm_parameter_value,
    is_aws_session_token_available,
)

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class ReCaptchaSettings(BaseModel):
    secret_key: str


class CleanUpSettings(BaseModel):
    user_pool_id: str
    grace_period_hours: Annotated[int, Ge(0)] = 24


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

        if self.recaptcha is not None:
            self.recaptcha.secret_key = get_required_aws_ssm_parameter_value(
                parameter_name=self.recaptcha.secret_key,
            )

        if self.cleanup is not None:
            self.cleanup.user_pool_id = get_required_aws_ssm_parameter_value(
                parameter_name=self.cleanup.user_pool_id,
            )

    recaptcha: Optional[ReCaptchaSettings] = None
    cleanup: Optional[CleanUpSettings] = None
