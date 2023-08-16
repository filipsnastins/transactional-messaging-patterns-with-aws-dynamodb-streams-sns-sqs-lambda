import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
from transactional_outbox.outbox import PublishedMessage

from .time import str_to_datetime

logger = Logger()


def create_published_message_from_stream_record(record: DynamoDBRecord) -> PublishedMessage:
    if record.dynamodb and record.dynamodb.new_image:
        return PublishedMessage(
            message_id=uuid.UUID(record.dynamodb.new_image["MessageId"]),
            aggregate_id=uuid.UUID(record.dynamodb.new_image["AggregateId"]),
            correlation_id=uuid.UUID(record.dynamodb.new_image["CorrelationId"]),
            topic=record.dynamodb.new_image["Topic"],
            message=record.dynamodb.new_image["Message"],
            created_at=str_to_datetime(record.dynamodb.new_image["CreatedAt"]),
            is_dispatched=False,
            dispatched_at=None,
        )
    raise ValueError("PublishedMessage not created from stream record")
