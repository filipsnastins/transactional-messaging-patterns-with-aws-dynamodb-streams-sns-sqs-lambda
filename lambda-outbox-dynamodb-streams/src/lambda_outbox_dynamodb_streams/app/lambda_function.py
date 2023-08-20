import os

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.batch import AsyncBatchProcessor, EventType, async_process_partial_response
from aws_lambda_powertools.utilities.batch.types import PartialItemFailureResponse
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
    DynamoDBRecordEventName,
    DynamoDBStreamEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

from . import clients
from .dispatch import TopicsCache, dispatch_message, envelope_json_message
from .message import create_published_message_from_stream_record
from .outbox_repository import create_outbox_repository
from .settings import get_settings

logger = Logger()

settings = get_settings()
processor = AsyncBatchProcessor(event_type=EventType.DynamoDBStreams)
topics_cache = TopicsCache(topic_name_prefix=settings.aws_sns_topic_prefix)


# Moto doesn't work well when the item from the same table is updated -
# Lambda functions end up in an infinite loop; DynamoDB put_item operation gets stuck


async def async_record_handler(record: DynamoDBRecord) -> None:
    if record.event_name == DynamoDBRecordEventName.INSERT:
        published_message = create_published_message_from_stream_record(record)

        async with clients.get_sns_client() as sns_client:
            await dispatch_message(sns_client, published_message, envelope_json_message, topics_cache)

        if not os.getenv("OUTBOX_SKIP_MARK_MESSAGES_AS_DISPATCHED"):
            await create_outbox_repository().mark_as_dispatched(message_id=published_message.message_id)


@event_source(data_class=DynamoDBStreamEvent)  # pylint: disable=no-value-for-parameter
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext) -> PartialItemFailureResponse:
    return async_process_partial_response(
        event=event,  # type: ignore
        record_handler=async_record_handler,
        processor=processor,
        context=context,
    )
