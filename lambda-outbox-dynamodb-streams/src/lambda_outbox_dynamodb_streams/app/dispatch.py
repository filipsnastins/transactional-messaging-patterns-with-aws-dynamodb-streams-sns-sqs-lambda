import json
from typing import Awaitable, Callable

from aws_lambda_powertools.logging import Logger
from tomodachi.envelope.json_base import JsonBase
from transactional_outbox.outbox import PublishedMessage
from types_aiobotocore_sns import SNSClient

logger = Logger()

TopicName = str
TopicArn = str

EnvelopeHandler = Callable[[PublishedMessage], Awaitable[str]]


class TopicsCache:
    def __init__(self) -> None:
        self._topics: dict[TopicName, TopicArn] = {}

    async def get_or_create_topic(self, topic: str, client: SNSClient) -> str:
        topic_arn = self._topics.get(topic)
        if topic_arn is None:
            create_topic_response = await client.create_topic(Name=topic)
            topic_arn = create_topic_response["TopicArn"]
            self._topics[topic] = topic_arn
        return topic_arn


async def envelope_json_message(message: PublishedMessage) -> str:
    return await JsonBase.build_message(service={}, topic=message.topic, data=json.loads(message.message))


async def dispatch_sns_message(
    sns_client: SNSClient, message: PublishedMessage, envelope_handler: EnvelopeHandler, topics_cache: TopicsCache
) -> None:
    topic_arn = await topics_cache.get_or_create_topic(message.topic, sns_client)
    envelope = await envelope_handler(message)
    await sns_client.publish(Message=envelope, TopicArn=topic_arn)
    logger.info("sns_message_dispatched", message_id=message.message_id, topic_arn=topic_arn)
