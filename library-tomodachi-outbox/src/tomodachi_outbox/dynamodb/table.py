import structlog
from types_aiobotocore_dynamodb import DynamoDBClient

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_outbox_table(table_name: str, client: DynamoDBClient) -> None:
    try:
        await client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    "AttributeName": "PK",
                    "AttributeType": "S",
                },
                {
                    "AttributeName": "AggregateId",
                    "AttributeType": "S",
                },
                {
                    "AttributeName": "NotDispatched",
                    "AttributeType": "S",
                },
            ],
            KeySchema=[
                {
                    "AttributeName": "PK",
                    "KeyType": "HASH",
                },
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "AggregateIdIndex",
                    "KeySchema": [
                        {"AttributeName": "AggregateId", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "NotDispatchedMessagesIndex",
                    "KeySchema": [
                        {"AttributeName": "NotDispatched", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            StreamSpecification={
                "StreamEnabled": True,
                "StreamViewType": "NEW_AND_OLD_IMAGES",
            },
            BillingMode="PAY_PER_REQUEST",
        )
    except client.exceptions.ResourceInUseException:
        logger.info("dynamodb_outbox_table_already_exists", table_name=table_name)
    else:
        logger.info("dynamodb_outbox_table_created", table_name=table_name)
