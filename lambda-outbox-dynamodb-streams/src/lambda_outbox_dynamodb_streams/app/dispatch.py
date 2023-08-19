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
    def __init__(self, topic_name_prefix: str) -> None:
        self._topic_name_prefix = topic_name_prefix
        self._topics: dict[TopicName, TopicArn] = {}

    async def get_or_create_topic(self, topic: str, client: SNSClient) -> str:
        topic_arn = self._topics.get(topic)
        if topic_arn is None:
            create_topic_response = await client.create_topic(Name=self._prefix_topic(topic))
            topic_arn = create_topic_response["TopicArn"]
            self._topics[topic] = topic_arn
        return topic_arn

    def _prefix_topic(self, topic: str) -> str:
        return f"{self._topic_name_prefix}{topic}"


async def envelope_json_message(message: PublishedMessage) -> str:
    return await JsonBase.build_message(service={}, topic=message.topic, data=json.loads(message.message))


async def dispatch_message(
    client: SNSClient, message: PublishedMessage, envelope_handler: EnvelopeHandler, topics_cache: TopicsCache
) -> None:
    topic_arn = await topics_cache.get_or_create_topic(topic=message.topic, client=client)
    envelope = await envelope_handler(message)
    await client.publish(Message=envelope, TopicArn=topic_arn)
    logger.info("message_dispatched", message_id=message.message_id, topic_name=message.topic, topic_arn=topic_arn)
