import asyncio
import datetime
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any

import boto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBStreamEvent, StreamRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_sns import SNSClient
from tomodachi.envelope.json_base import JsonBase

logger = Logger()

region_name = os.environ["AWS_REGION"]
endpoint_url = os.environ["AWS_ENDPOINT_URL"]
table_name = os.environ["DYNAMODB_OUTBOX_TABLE_NAME"]


@dataclass
class Message:
    message_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime
    dispatched: bool = False
    dispatched_at: datetime.datetime | None = None

    @staticmethod
    def from_stream_record(record: StreamRecord | dict[str, Any]) -> "Message":
        return Message(
            message_id=uuid.UUID(record["MessageId"]),
            aggregate_id=uuid.UUID(record["AggregateId"]),
            correlation_id=uuid.UUID(record["CorrelationId"]),
            topic=record["Topic"],
            message=record["Message"],
            created_at=datetime.datetime.fromisoformat(record["CreatedAt"]),
        )


def get_dynamodb_client() -> DynamoDBClient:
    return boto3.client("dynamodb", region_name=region_name, endpoint_url=endpoint_url)


def get_sns_client() -> SNSClient:
    return boto3.client("sns", region_name=region_name, endpoint_url=endpoint_url)


@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext) -> None:
    for record in event.records:
        if new_image := record.dynamodb and record.dynamodb.new_image:
            message = Message.from_stream_record(new_image)
            logger.info("received_message", message_id=str(message.message_id))

            envelope = asyncio.get_event_loop().run_until_complete(
                JsonBase.build_message(
                    service={},
                    topic=message.topic,
                    data=json.loads(message.message),
                )
            )
            logger.info("enveloped_message", message_id=str(message.message_id))

            sns_client = get_sns_client()
            create_topic_response = sns_client.create_topic(Name=message.topic)
            topic_arn = create_topic_response["TopicArn"]
            logger.info("topic_created", message_id=str(message.message_id), topic_arn=topic_arn)

            sns_client.publish(Message=envelope, TopicArn=topic_arn)
            logger.info("message_dispatched", message_id=str(message.message_id), topic_arn=topic_arn)
