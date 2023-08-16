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
from .dispatch import TopicsCache, dispatch_sns_message, envelope_json_message
from .message import create_published_message_from_stream_record

logger = Logger()

processor = AsyncBatchProcessor(event_type=EventType.DynamoDBStreams)
topics_cache = TopicsCache()


async def async_record_handler(record: DynamoDBRecord) -> None:
    if record.event_name != DynamoDBRecordEventName.INSERT:
        logger.info("not_dynamodb_insert_event", dynamodb_event_name=record.event_name)
        return

    published_message = create_published_message_from_stream_record(record)

    async with clients.get_sns_client() as sns_client:
        await dispatch_sns_message(sns_client, published_message, envelope_json_message, topics_cache)

    # FIXME: Moto doesn't work well when the item from the same table is updated -
    # Lambda functions end up in an infinite loop; put_item operation to DynamoDB gets stuck

    # outbox_repository = create_outbox_repository()
    # await outbox_repository.mark_dispatched(message_id=published_message.message_id)


@event_source(data_class=DynamoDBStreamEvent)  # pylint: disable=no-value-for-parameter
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext) -> PartialItemFailureResponse:
    return async_process_partial_response(
        event=event,  # type: ignore
        record_handler=async_record_handler,
        processor=processor,
        context=context,
    )
