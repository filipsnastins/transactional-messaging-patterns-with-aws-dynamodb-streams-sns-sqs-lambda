import datetime
import json
import uuid
from dataclasses import dataclass
from typing import Protocol

import structlog
from adapters import dynamodb
from customers.events import Event

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
    def __init__(self, table_name: str, session: dynamodb.DynamoDBSession, topics: dict[type[Event], str]) -> None:
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
                            "EventId": {"S": str(event.event_id)},
                            "Topic": {"S": topic},
                            "Message": {"S": json.dumps(event.to_dict())},
                            "CreatedAt": {"S": event.created_at.isoformat()},
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

    async def get(self, event_id: uuid.UUID) -> SavedEvent | None:
        async with dynamodb.get_dynamodb_client() as client:
            response = await client.get_item(
                TableName=self.table_name,
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
