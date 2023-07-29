import abc
from typing import Any

import structlog
from adapters import dynamodb
from adapters.customer_repository import AbstractCustomerRepository, DynamoDBCustomerRepository
from adapters.event_repository import AbstractEventRepository, DynamoDBEventRepository
from service_layer.topics import CUSTOMER_TOPICS_MAP
from tomodachi.envelope.json_base import JsonBase

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class AbstractUnitOfWork(abc.ABC):
    customers: AbstractCustomerRepository
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
    customers: DynamoDBCustomerRepository
    events: DynamoDBEventRepository

    def __init__(
        self,
        session: dynamodb.DynamoDBSession,
        customers: DynamoDBCustomerRepository,
        events: DynamoDBEventRepository,
    ) -> None:
        self.session = session
        self.customers = customers
        self.events = events

    @staticmethod
    def create() -> "DynamoDBUnitOfWork":
        session = dynamodb.DynamoDBSession()
        customers = DynamoDBCustomerRepository(session)
        events = DynamoDBEventRepository(session, envelope=JsonBase(), topics=CUSTOMER_TOPICS_MAP)
        return DynamoDBUnitOfWork(session, customers, events)

    async def commit(self) -> None:
        items = self.session.get()
        if not items:
            logger.debug("dynamodb_unit_of_work__nothing_to_commit")
            return
        async with dynamodb.get_dynamodb_client() as client:
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
