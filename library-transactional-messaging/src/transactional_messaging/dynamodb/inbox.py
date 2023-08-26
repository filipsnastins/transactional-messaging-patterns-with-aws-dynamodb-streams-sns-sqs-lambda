import uuid

import structlog
from types_aiobotocore_dynamodb import DynamoDBClient
from unit_of_work.dynamodb import DynamoDBSession

from transactional_messaging.idempotent_consumer import InboxRepository, MessageAlreadyProcessedError, ProcessedMessage
from transactional_messaging.utils.time import datetime_to_str, str_to_datetime, utcnow

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class DynamoDBInboxRepository(InboxRepository):
    def __init__(self, table_name: str, session: DynamoDBSession) -> None:
        self._table_name = table_name
        self._session = session

    async def save(self, message_id: uuid.UUID) -> None:
        self._session.add(
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        "PK": {"S": f"MESSAGE#{message_id}"},
                        "MessageId": {"S": str(message_id)},
                        "CreatedAt": {"S": datetime_to_str(utcnow())},
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            raise_on_condition_check_failure=MessageAlreadyProcessedError(message_id),
        )
        logger.info("dynamodb_inbox_repository__processed_message_saved", message_id=message_id)

    async def get(self, message_id: uuid.UUID) -> ProcessedMessage | None:
        async with self._session.get_client() as client:
            response = await client.get_item(
                TableName=self._table_name,
                Key={"PK": {"S": f"MESSAGE#{message_id}"}},
                ConsistentRead=True,  # ConsistentRead is required to ensure idempotence
            )
            item = response.get("Item")
            if not item:
                return None
            return ProcessedMessage(
                message_id=uuid.UUID(item["MessageId"]["S"]),
                created_at=str_to_datetime(item["CreatedAt"]["S"]),
            )


async def create_inbox_table(table_name: str, client: DynamoDBClient) -> None:
    try:
        await client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    "AttributeName": "PK",
                    "AttributeType": "S",
                },
            ],
            KeySchema=[
                {
                    "AttributeName": "PK",
                    "KeyType": "HASH",
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except client.exceptions.ResourceInUseException:
        logger.info("dynamodb_inbox_table_already_exists", table_name=table_name)
    else:
        logger.info("dynamodb_inbox_table_created", table_name=table_name)
