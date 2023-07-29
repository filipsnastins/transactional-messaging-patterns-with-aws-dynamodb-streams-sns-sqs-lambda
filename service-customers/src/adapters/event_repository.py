import datetime
import uuid
from dataclasses import dataclass
from typing import Protocol

import structlog
from adapters import dynamodb
from customers.events import Event
from tomodachi.envelope.json_base import JsonBase

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class EventAlreadyPublishedError(Exception):
    pass


@dataclass
class SavedEvent:
    event_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime
    published_at: datetime.datetime | None = None


class AbstractEventRepository(Protocol):
    async def publish(self, events: list[Event]) -> None:
        ...

    async def get(self, event_id: uuid.UUID) -> SavedEvent | None:
        ...


class DynamoDBEventRepository(AbstractEventRepository):
    def __init__(self, session: dynamodb.DynamoDBSession, envelope: JsonBase, topics: dict[type[Event], str]) -> None:
        self.session = session
        self.envelope = envelope
        self.topics = topics

    async def publish(self, events: list[Event]) -> None:
        for event in events:
            await self._publish(event)

    async def get(self, event_id: uuid.UUID) -> SavedEvent | None:
        async with dynamodb.get_dynamodb_client() as client:
            response = await client.get_item(
                TableName=dynamodb.get_table_name(),
                Key={"PK": {"S": f"EVENT#{event_id}"}},
            )
            item = response.get("Item")
            if not item:
                logger.debug("dynamodb_event_repository__event_not_found", event_id=event_id)
                return None
            if published_at := item.get("PublishedAt"):
                published_at = datetime.datetime.fromisoformat(published_at["S"])
            else:
                published_at = None
            return SavedEvent(
                event_id=uuid.UUID(item["EventId"]["S"]),
                topic=item["Topic"]["S"],
                message=item["Message"]["S"],
                created_at=datetime.datetime.fromisoformat(item["CreatedAt"]["S"]),
                published_at=published_at,
            )

    async def _publish(self, event: Event) -> None:
        topic = self._get_topic(type(event))
        message = await self._build_message(event=event, topic=topic)
        self.session.add(
            {
                "ConditionCheck": {
                    "TableName": dynamodb.get_table_name(),
                    "Key": {"PK": {"S": f"EVENT#{event.event_id}"}},
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            raise_on_condition_check_failure=EventAlreadyPublishedError(event.event_id),
        )
        self.session.add(
            {
                "Put": {
                    "TableName": dynamodb.get_table_name(),
                    "Item": {
                        "PK": {"S": f"EVENT#{event.event_id}"},
                        "EventId": {"S": str(event.event_id)},
                        "Topic": {"S": topic},
                        "Message": {"S": message},
                        "CreatedAt": {"S": event.created_at.isoformat()},
                    },
                }
            }
        )
        logger.info(
            "dynamodb_event_repository__event_published",
            event_id=event.event_id,
            event_type=type(event),
            topic=topic,
        )

    def _get_topic(self, event_type: type[Event]) -> str:
        return self.topics[event_type]

    async def _build_message(self, event: Event, topic: str) -> str:
        return await self.envelope.build_message(
            service={},
            topic=topic,
            data=event.to_dict(),
        )
