from typing import Literal, Optional

from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

import src.adapters.aws as aws_adapter

ContactAttributes = Literal["email", "phone_number"]

_VerifiedAttributeMap: dict[ContactAttributes, str] = {
    "email": "email_verified",
    "phone_number": "phone_number_verified",
}


def is_contact_in_use(
    cognito_client: CognitoIdentityProviderClient,
    user_pool_id: str,
    attribute_name: ContactAttributes,
    attribute_value: Optional[str],
) -> bool:
    if not attribute_value:
        return False

    pagination_token: Optional[str] = None
    try:
        while True:
            params = {
                "UserPoolId": user_pool_id,
                "Filter": f'{attribute_name} = "{attribute_value}"',
                "Limit": 60,
            }
            if pagination_token:
                params["PaginationToken"] = pagination_token

            response = cognito_client.list_users(**params)
            for user in response.get("Users", []):
                if aws_adapter.is_user_attributed_verified(
                    user, _VerifiedAttributeMap[attribute_name]
                ):
                    return True

            pagination_token = response.get("PaginationToken")
            if not pagination_token:
                break
    except (BotoCoreError, ClientError) as exc:
        raise ValueError(
            "Unable to validate contact information. Please try again."
        ) from exc

    return False
