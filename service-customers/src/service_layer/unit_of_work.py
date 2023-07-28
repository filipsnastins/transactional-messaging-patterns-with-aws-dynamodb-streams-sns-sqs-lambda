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
        if not items:
            return None
        async with dynamodb.get_dynamodb_client() as client:
            try:
                transact_items = [item["transact_item"] for item in items]
                await client.transact_write_items(TransactItems=transact_items)
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
        self.customers.session.clear()
