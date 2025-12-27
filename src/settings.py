import urllib.request
import urllib.parse
import os
import json
from typing import Any, Optional

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


AwsSessionToken = os.getenv("AWS_SESSION_TOKEN", "")


def get_aws_ssm_parameter(
    parameter_name: str, aws_session_token: str = AwsSessionToken
) -> Any:
    print(f"Fetching SSM parameter: {parameter_name}")
    url_encoded_name = urllib.parse.quote_plus(parameter_name, encoding="utf-8")
    request = urllib.request.Request(
        f"http://localhost:2773/systemsmanager/parameters/get?name={url_encoded_name}&withDecryption=true"
    )
    request.add_header("X-Aws-Parameters-Secrets-Token", aws_session_token)
    json_value = urllib.request.urlopen(request).read()

    return json.loads(json_value)


def get_aws_ssm_parameter_value(
    parameter_name: str, aws_session_token: str = AwsSessionToken
) -> Optional[str]:
    parameter = get_aws_ssm_parameter(
        parameter_name=parameter_name,
        aws_session_token=aws_session_token,
    ).get("Parameter", {})

    if "Value" not in parameter:
        raise KeyError(
            f"Parameter {parameter_name} does not have a Value field"
        )

    return parameter.get("Value")


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
        if not AwsSessionToken:
            return
        # Override secret_key with value from AWS SSM
        if self.recaptcha.secret_key is not None:
            self.recaptcha.secret_key = get_aws_ssm_parameter_value(
                parameter_name=self.recaptcha.secret_key,
                aws_session_token=AwsSessionToken,
            )

    recaptcha: ReCaptchaSettings
