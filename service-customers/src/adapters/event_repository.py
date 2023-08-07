import datetime
import json
import uuid
from typing import Protocol

import structlog

from adapters import clients, dynamodb
from customers.events import Event
from tomodachi_outbox.message import Message

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

TopicsMap = dict[type[Event], str]


class EventAlreadyPublishedError(Exception):
    pass


class AbstractEventRepository(Protocol):
    async def publish(self, events: list[Event]) -> None:
        ...

    async def get(self, event_id: uuid.UUID) -> Message | None:
        ...


class DynamoDBEventRepository(AbstractEventRepository):
    def __init__(self, table_name: str, session: dynamodb.DynamoDBSession, topics: TopicsMap) -> None:
        self.table_name = table_name
        self.session = session
        self.topics = topics

    async def publish(self, events: list[Event]) -> None:
        for event in events:
            topic = self.topics[type(event)]
            self.session.add(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": {
                            "PK": {"S": f"EVENT#{event.event_id}"},
                            "MessageId": {
                                "S": str(event.event_id)
                            },  # TODO MessageId; split into event and command outbox
                            "AggregateId": {"S": str(event.customer_id)},
                            "CorrelationId": {"S": str(event.correlation_id)},
                            "Topic": {"S": topic},
                            "Message": {"S": json.dumps(event.to_dict())},
                            "CreatedAt": {"S": event.created_at.isoformat()},
                            "Dispatched": {"BOOL": False},
                            "DispatchedAt": {"NULL": True},
                        },
                        "ConditionExpression": "attribute_not_exists(PK)",
                    }
                },
                raise_on_condition_check_failure=EventAlreadyPublishedError(event.event_id),
            )
            logger.info(
                "dynamodb_event_repository__event_published",
                event_id=event.event_id,
                event_type=type(event),
                topic=topic,
            )

    async def get(self, event_id: uuid.UUID) -> Message | None:
        async with clients.get_dynamodb_client() as client:
            response = await client.get_item(TableName=self.table_name, Key={"PK": {"S": f"EVENT#{event_id}"}})
            item = response.get("Item")
            if not item:
                logger.debug("dynamodb_event_repository__event_not_found", event_id=event_id)
                return None
            dispatched_at = (
                datetime.datetime.fromisoformat(item["DispatchedAt"]["S"]) if item["DispatchedAt"].get("S") else None
            )
            return Message(
                message_id=uuid.UUID(item["MessageId"]["S"]),  # TODO MessageId
                aggregate_id=uuid.UUID(item["AggregateId"]["S"]),
                correlation_id=uuid.UUID(item["CorrelationId"]["S"]),
                topic=item["Topic"]["S"],
                message=item["Message"]["S"],
                created_at=datetime.datetime.fromisoformat(item["CreatedAt"]["S"]),
            )
