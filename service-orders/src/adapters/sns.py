import structlog

from adapters import clients

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_topics() -> None:
    async with clients.get_sns_client() as client:
        await client.create_topic(Name="customer--credit-reservation-failed")
        await client.create_topic(Name="customer--credit-reserved")
        await client.create_topic(Name="order--cancelled")
        await client.create_topic(Name="order--created")

    logger.info("sns_topics_created")
