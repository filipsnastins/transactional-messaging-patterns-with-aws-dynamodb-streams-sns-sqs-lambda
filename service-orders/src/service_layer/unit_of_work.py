import abc
from typing import Any

import structlog

from adapters import clients, dynamodb
from adapters.event_repository import AbstractEventRepository, DynamoDBEventRepository
from adapters.order_repository import AbstractOrderRepository, DynamoDBOrderRepository
from service_layer.topics import TOPICS_MAP

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class AbstractUnitOfWork(abc.ABC):
    orders: AbstractOrderRepository
    events: AbstractEventRepository

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.rollback()

    @abc.abstractmethod
    async def commit(self) -> None:
        pass

    @abc.abstractmethod
    async def rollback(self) -> None:
        pass


class DynamoDBUnitOfWork(AbstractUnitOfWork):
    session: dynamodb.DynamoDBSession
    orders: DynamoDBOrderRepository
    events: DynamoDBEventRepository

    def __init__(
        self, session: dynamodb.DynamoDBSession, orders: DynamoDBOrderRepository, events: DynamoDBEventRepository
    ) -> None:
        self.session = session
        self.orders = orders
        self.events = events

    @staticmethod
    def create() -> "DynamoDBUnitOfWork":
        session = dynamodb.DynamoDBSession()
        customers = DynamoDBOrderRepository(dynamodb.get_aggregate_table_name(), session)
        events = DynamoDBEventRepository(dynamodb.get_outbox_table_name(), session, TOPICS_MAP)
        return DynamoDBUnitOfWork(session, customers, events)

    async def commit(self) -> None:
        items = self.session.get()
        if not items:
            logger.debug("dynamodb_unit_of_work__nothing_to_commit")
            return
        async with clients.get_dynamodb_client() as client:
            try:
                transact_items = [item["transact_item"] for item in items]
                await client.transact_write_items(TransactItems=transact_items)
                logger.debug("dynamodb_unit_of_work__committed", item_count=len(items))
            except client.exceptions.TransactionCanceledException as e:
                cancellation_codes = [reason["Code"] for reason in e.response["CancellationReasons"]]
                raise_on_condition_failures = [item["raise_on_condition_check_failure"] for item in items]
                zipped = zip(cancellation_codes, raise_on_condition_failures)
                for cancellation_code, raise_on_condition_failure in zipped:
                    if cancellation_code == "None":
                        continue
                    if cancellation_code == "ConditionalCheckFailed" and raise_on_condition_failure is not None:
                        raise raise_on_condition_failure from e
                raise
            finally:
                await self.rollback()

    async def rollback(self) -> None:
        self.session.clear()
        logger.debug("dynamodb_unit_of_work__rollbacked")