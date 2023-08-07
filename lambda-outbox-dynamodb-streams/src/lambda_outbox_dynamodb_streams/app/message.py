import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import StreamRecord


@dataclass
class Message:
    message_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime

    @staticmethod
    def from_stream_record(record: StreamRecord | dict[str, Any]) -> "Message":
        return Message(
            message_id=uuid.UUID(record["MessageId"]),
            aggregate_id=uuid.UUID(record["AggregateId"]),
            correlation_id=uuid.UUID(record["CorrelationId"]),
            topic=record["Topic"],
            message=record["Message"],
            created_at=datetime.datetime.fromisoformat(record["CreatedAt"]).replace(tzinfo=datetime.timezone.utc),
        )
