import asyncio
import json
import os

import boto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecordEventName,
    DynamoDBStreamEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_sns import SNSClient
from tomodachi.envelope.json_base import JsonBase

from .message import Message

logger = Logger()

region_name = os.environ["AWS_REGION"]
endpoint_url = os.environ["AWS_ENDPOINT_URL"]


def get_sns_client() -> SNSClient:
    return boto3.client("sns", region_name=region_name, endpoint_url=endpoint_url)


@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext) -> None:
    for record in event.records:
        if record.event_name != DynamoDBRecordEventName.INSERT:
            logger.debug("not_dynamodb_insert_event", event_name=record.event_name)
            continue

        if new_image := record.dynamodb and record.dynamodb.new_image:
            message = Message.from_stream_record(new_image)
            logger.info("received_message", message_id=message.message_id)

            envelope = asyncio.get_event_loop().run_until_complete(
                JsonBase.build_message(
                    service={},
                    topic=message.topic,
                    data=json.loads(message.message),
                )
            )
            logger.info("enveloped_message", message_id=message.message_id)

            sns_client = get_sns_client()
            create_topic_response = sns_client.create_topic(Name=message.topic)
            topic_arn = create_topic_response["TopicArn"]
            logger.info("topic_created", message_id=message.message_id, topic_arn=topic_arn)

            sns_client.publish(Message=envelope, TopicArn=topic_arn)
            logger.info("message_dispatched", message_id=message.message_id, topic_arn=topic_arn)
