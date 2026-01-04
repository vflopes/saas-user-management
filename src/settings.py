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


class UsersTableSettings(BaseModel):
    name: str
    expire_unverified_users_minutes: Annotated[int, Ge(0)] = 360


class UserPoolSettings(BaseModel):
    id: str


class PosthogSettings(BaseModel):
    api_key: str
    api_host: str = "https://app.posthog.com"


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

        if self.user_pool is not None:
            self.user_pool.id = get_required_aws_ssm_parameter_value(
                parameter_name=self.user_pool.id,
            )

        if self.posthog is not None:
            self.posthog.api_key = get_required_aws_ssm_parameter_value(
                parameter_name=self.posthog.api_key,
            )
            self.posthog.api_host = get_required_aws_ssm_parameter_value(
                parameter_name=self.posthog.api_host,
            )

    recaptcha: Optional[ReCaptchaSettings] = None
    cleanup: Optional[CleanUpSettings] = None
    users_table: Optional[UsersTableSettings] = None
    user_pool: Optional[UserPoolSettings] = None
    posthog: Optional[PosthogSettings] = None

    def ensure_users_table_settings(self) -> UsersTableSettings:
        users_table = self.users_table
        if not users_table:
            raise ValueError("Users table is not configured.")
        return users_table

    def ensure_recaptcha_settings(self) -> ReCaptchaSettings:
        if not self.recaptcha:
            raise ValueError("reCAPTCHA secret key is not configured.")
        return self.recaptcha

    def ensure_user_pool_settings(self) -> UserPoolSettings:
        if not self.user_pool:
            raise ValueError("User pool is not configured.")
        return self.user_pool
