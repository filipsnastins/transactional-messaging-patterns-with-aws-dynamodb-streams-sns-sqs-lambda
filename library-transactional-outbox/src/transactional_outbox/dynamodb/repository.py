import uuid
from typing import Any

import structlog
from unit_of_work.dynamodb import DynamoDBSession

from transactional_outbox.repository import Message, MessageAlreadyPublishedError, OutboxRepository, PublishedMessage
from transactional_outbox.utils.time import datetime_to_str, str_to_datetime, utcnow

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class UnknownTopicError(Exception):
    pass


class DynamoDBOutboxRepository(OutboxRepository):
    def __init__(self, table_name: str, session: DynamoDBSession, topic_map: dict[type[Any], str]) -> None:
        self._table_name = table_name
        self._session = session
        self._topics_map = topic_map

    async def publish(self, messages: list[Message]) -> None:
        for message in messages:
            topic = self._get_topic(message)
            self._session.add(
                {
                    "Put": {
                        "TableName": self._table_name,
                        "Item": {
                            "PK": {"S": f"MESSAGE#{message.message_id}"},
                            "MessageId": {"S": str(message.message_id)},
                            "AggregateId": {"S": str(message.aggregate_id)},
                            "CorrelationId": {"S": str(message.correlation_id)},
                            "Topic": {"S": topic},
                            "Message": {"S": message.serialize()},
                            "CreatedAt": {"S": datetime_to_str(message.created_at)},
                            "NotDispatched": {"S": "Y"},
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
                message_name=message.__class__.__name__,
                topic=topic,
            )

    async def get(self, message_id: uuid.UUID) -> PublishedMessage | None:
        async with self._session.get_client() as client:
            response = await client.get_item(
                TableName=self._table_name,
                Key={"PK": {"S": f"MESSAGE#{message_id}"}},
            )
            item = response.get("Item")
            if not item:
                logger.error("dynamodb_message_repository__message_not_found", message_id=message_id)
                return None
            return self._item_to_published_message(item)

    async def mark_dispatched(self, message_id: uuid.UUID) -> None:
        async with self._session.get_client() as client:
            await client.update_item(
                TableName=self._table_name,
                Key={"PK": {"S": f"MESSAGE#{message_id}"}},
                UpdateExpression="REMOVE NotDispatched SET IsDispatched = :IsDispatched, DispatchedAt = :DispatchedAt",
                ExpressionAttributeValues={
                    ":IsDispatched": {"BOOL": True},
                    ":DispatchedAt": {"S": datetime_to_str(utcnow())},
                },
            )
            logger.info("dynamodb_message_repository__message_marked_as_dispatched", message_id=message_id)

    async def get_not_dispatched_messages(self) -> list[PublishedMessage]:
        async with self._session.get_client() as client:
            response = await client.query(
                TableName=self._table_name,
                IndexName="NotDispatchedMessagesIndex",
                KeyConditionExpression="NotDispatched = :NotDispatched",
                ExpressionAttributeValues={":NotDispatched": {"S": "Y"}},
            )
            if not response["Items"]:
                return []
            items = response["Items"]
            return [self._item_to_published_message(item) for item in items]

    def _get_topic(self, message: Message) -> str:
        try:
            return self._topics_map[type(message)]
        except KeyError as e:
            message_name = message.__class__.__name__
            logger.error("dynamodb_message_repository__unknown_topic", message_name=message_name)
            raise UnknownTopicError(message_name) from e

    def _item_to_published_message(self, item: dict[str, Any]) -> PublishedMessage:
        return PublishedMessage(
            message_id=uuid.UUID(item["MessageId"]["S"]),
            aggregate_id=uuid.UUID(item["AggregateId"]["S"]),
            correlation_id=uuid.UUID(item["CorrelationId"]["S"]),
            topic=item["Topic"]["S"],
            message=item["Message"]["S"],
            created_at=str_to_datetime(item["CreatedAt"]["S"]),
            is_dispatched=bool(item["IsDispatched"]["BOOL"]) if item.get("IsDispatched") else False,
            dispatched_at=str_to_datetime(item["DispatchedAt"]["S"]) if item.get("DispatchedAt") else None,
        )
