from datetime import datetime
from mypy_boto3_dynamodb import DynamoDBClient


def set_user_as_verified(
    dynamodb_client: DynamoDBClient,
    user_table_name: str,
    user_id: str,
    now: datetime,
):
    dynamodb_client.update_item(
        TableName=user_table_name,
        Key={"user_id": {"S": user_id}},
        UpdateExpression="SET verified_at = :verified_at REMOVE expires_at",
        ExpressionAttributeValues={
            ":verified_at": {"N": str(int(now.timestamp()))}
        },
    )
