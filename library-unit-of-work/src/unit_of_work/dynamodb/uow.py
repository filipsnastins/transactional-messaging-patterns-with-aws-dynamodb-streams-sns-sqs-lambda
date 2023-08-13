import structlog

from unit_of_work.dynamodb.client import DynamoDBClientFactory
from unit_of_work.dynamodb.session import DynamoDBSession
from unit_of_work.uow import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class BaseDynamoDBUnitOfWork(AbstractUnitOfWork):
    session: DynamoDBSession

    def __init__(self, client_factory: DynamoDBClientFactory) -> None:
        self.session = DynamoDBSession(client_factory)

    async def commit(self) -> None:
        await self.session.commit()
        logger.debug("dynamodb_unit_of_work__committed")

    async def rollback(self) -> None:
        self.session.rollback()
        logger.debug("dynamodb_unit_of_work__rolled_back")
