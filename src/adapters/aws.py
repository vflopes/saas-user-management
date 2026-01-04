import boto3

from typing import Optional

from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_cognito_idp.type_defs import UserTypeTypeDef
from mypy_boto3_dynamodb import DynamoDBClient

_cognito_client: Optional[CognitoIdentityProviderClient] = None


def get_cognito_client() -> CognitoIdentityProviderClient:
    global _cognito_client
    if not _cognito_client:
        _cognito_client = boto3.client("cognito-idp")
    return _cognito_client


_dynamodb_client: Optional[DynamoDBClient] = None


def get_dynamodb_client() -> DynamoDBClient:
    global _dynamodb_client
    if not _dynamodb_client:
        _dynamodb_client = boto3.client("dynamodb")
    return _dynamodb_client


def get_attribute_value(user: UserTypeTypeDef, name: str) -> str:
    for attribute in user.get("Attributes", []):
        if attribute.get("Name") == name:
            return attribute.get("Value", "")
    return ""


def is_user_attributed_verified(
    user: UserTypeTypeDef, verified_attr_name: str
) -> bool:
    return get_attribute_value(user, verified_attr_name).lower() == "true"
