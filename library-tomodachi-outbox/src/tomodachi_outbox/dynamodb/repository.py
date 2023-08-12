import uuid

import structlog

from tomodachi_outbox.dynamodb.client import DynamoDBClientFactory
from tomodachi_outbox.dynamodb.session import DynamoDBSession
from tomodachi_outbox.repository import Message, MessageAlreadyPublishedError, OutboxRepository, PublishedMessage
from tomodachi_outbox.utils.time import datetime_to_str, str_to_datetime

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

TopicsMap = dict[type[Message], str]


class DynamoDBOutboxRepository(OutboxRepository):
    def __init__(
        self, client_factory: DynamoDBClientFactory, session: DynamoDBSession, table_name: str, topics: TopicsMap
    ) -> None:
        self.get_client = client_factory
        self.session = session
        self.table_name = table_name
        self.topics = topics

    async def publish(self, messages: list[Message]) -> None:
        for message in messages:
            topic = self.topics[type(message)]
            self.session.add(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": {
                            "PK": {"S": f"MESSAGE#{message.message_id}"},
                            "MessageId": {"S": str(message.message_id)},
                            "AggregateId": {"S": str(message.aggregate_id)},
                            "CorrelationId": {"S": str(message.correlation_id)},
                            "Topic": {"S": topic},
                            "Message": {"S": message.serialize()},
                            "CreatedAt": {"S": datetime_to_str(message.created_at)},
                        },
                        "ConditionExpression": "attribute_not_exists(PK)",
                    }
                },
                raise_on_condition_check_failure=MessageAlreadyPublishedError(message.message_id),
            )
            logger.info(
                "dynamodb_message_repository__message_published",
                message_id=message.message_id,
                aggregate_id=message.aggregate_id,
                message=type(message),
                topic=topic,
            )

    async def get(self, message_id: uuid.UUID) -> PublishedMessage | None:
        async with self.get_client() as client:
            response = await client.get_item(TableName=self.table_name, Key={"PK": {"S": f"MESSAGE#{message_id}"}})
            item = response.get("Item")
            if not item:
                logger.debug("dynamodb_message_repository__message_not_found", message_id=message_id)
                return None
            return PublishedMessage(
                message_id=uuid.UUID(item["MessageId"]["S"]),
                aggregate_id=uuid.UUID(item["AggregateId"]["S"]),
                correlation_id=uuid.UUID(item["CorrelationId"]["S"]),
                topic=item["Topic"]["S"],
                message=item["Message"]["S"],
                created_at=str_to_datetime(item["CreatedAt"]["S"]),
                is_dispatched=False,
                dispatched_at=None,
            )

    async def mark_dispatched(self, message_id: uuid.UUID) -> None:
        raise NotImplementedError

    async def get_not_dispatched_messages(self) -> list[PublishedMessage]:
        raise NotImplementedError
