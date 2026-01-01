import boto3

from typing import Callable

from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_cognito_idp.type_defs import UserTypeTypeDef


def get_cognito_client() -> Callable[[], CognitoIdentityProviderClient]:
    cognito_client = boto3.client("cognito-idp")
    return lambda: cognito_client


def get_attribute_value(user: UserTypeTypeDef, name: str) -> str:
    for attribute in user.get("Attributes", []):
        if attribute.get("Name") == name:
            return attribute.get("Value", "")
    return ""


def is_attributed_verified(
    user: UserTypeTypeDef, verified_attr_name: str
) -> bool:
    return get_attribute_value(user, verified_attr_name).lower() == "true"
