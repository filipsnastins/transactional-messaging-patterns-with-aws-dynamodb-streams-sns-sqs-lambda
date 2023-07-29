import structlog
from customers.events import CustomerCreatedEvent, Event
from structlog import get_logger
from tomodachi import aws_sns_sqs_publish, get_service
from tomodachi.envelope.json_base import JsonBase

logger: structlog.stdlib.BoundLogger = get_logger()


EVENT_TO_TOPIC = {
    CustomerCreatedEvent: "customer--created",
}


async def publish(events: list[Event]) -> None:
    for event in events:
        topic = EVENT_TO_TOPIC[type(event)]
        data = event.to_dict()
        await aws_sns_sqs_publish(
            service=get_service(),
            data=data,
            topic=topic,
            message_envelope=JsonBase,
        )
        logger.info(
            "event_published",
            topic=topic,
            event_id=event.event_id,
            event_name=event.__class__.__name__,
        )
