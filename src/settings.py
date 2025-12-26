import urllib.request
import urllib.parse
import os
import json
from typing import Any, Optional
from typing_extensions import Self

from pydantic import (
    Field,
)

from pydantic import BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


AwsSessionToken = os.getenv("AWS_SESSION_TOKEN", "")


def get_aws_ssm_parameter(
    parameter_name: str, aws_session_token: str = AwsSessionToken
) -> Any:
    url_encoded_name = urllib.parse.quote(parameter_name, safe="")
    request = urllib.request.Request(
        f"http://localhost:2773/systemsmanager/parameters/get?name={url_encoded_name}&withDecryption=true"
    )
    request.add_header("X-Aws-Parameters-Secrets-Token", aws_session_token)
    json_value = urllib.request.urlopen(request).read()

    return json.loads(json_value)


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

    @model_validator(mode="after")
    def aws_ssm_parameter_store(self) -> Self:
        if not AwsSessionToken:
            return self
        # Override secret_key with value from AWS SSM
        if self.recaptcha.secret_key is not None:
            self.recaptcha.secret_key = get_aws_ssm_parameter(
                parameter_name=self.recaptcha.secret_key,
                aws_session_token=AwsSessionToken,
            )

        return self

    recaptcha: ReCaptchaSettings
