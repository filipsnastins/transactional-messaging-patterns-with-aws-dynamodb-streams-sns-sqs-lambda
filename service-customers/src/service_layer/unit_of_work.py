import abc
from typing import Any

from adapters import dynamodb
from adapters.repository import AbstractRepository, DynamoDBRepository, DynamoDBSession


class AbstractUnitOfWork(abc.ABC):
    customers: AbstractRepository

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
    customers: DynamoDBRepository

    def __init__(self, customers: DynamoDBRepository) -> None:
        self.customers = customers

    @staticmethod
    def create() -> "DynamoDBUnitOfWork":
        session = DynamoDBSession()
        customers = DynamoDBRepository(session)
        return DynamoDBUnitOfWork(customers)

    async def commit(self) -> None:
        items = self.customers.session.get()
        if items:
            transact_items = [item["transact_item"] for item in items]
            domain_exceptions = [item["domain_exception"] for item in items]
            async with dynamodb.get_dynamodb_client() as client:
                try:
                    await client.transact_write_items(TransactItems=transact_items)
                except client.exceptions.TransactionCanceledException as e:
                    cancellation_reasons = e.response["CancellationReasons"]
                    for cancellation_reason, domain_exception in zip(cancellation_reasons, domain_exceptions):
                        if cancellation_reason["Code"] == "None":
                            continue
                        if cancellation_reason["Code"] == "ConditionalCheckFailed" and domain_exception is not None:
                            raise domain_exception from e
                    raise
                finally:
                    await self.rollback()

    async def rollback(self) -> None:
        self.customers.session.clear()
