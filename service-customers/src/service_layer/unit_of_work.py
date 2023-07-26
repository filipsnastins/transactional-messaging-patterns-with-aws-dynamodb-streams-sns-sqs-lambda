import abc
from typing import Any

from adapters import dynamodb
from adapters.repository import AbstractCustomersRepository, DynamoDBCustomersRepository
from types_aiobotocore_dynamodb.client import BotocoreClientError


class AbstractUnitOfWork(abc.ABC):
    customers: AbstractCustomersRepository

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


class DynamoDBCommitError(BotocoreClientError):
    pass


class DynamoDBUnitOfWork(AbstractUnitOfWork):
    customers: DynamoDBCustomersRepository

    def __init__(self) -> None:
        self.customers = DynamoDBCustomersRepository()

    async def commit(self) -> None:
        items = self.customers.session.get()
        if items:
            async with dynamodb.get_dynamodb_client() as client:
                try:
                    await client.transact_write_items(TransactItems=items)
                except client.exceptions.TransactionCanceledException as e:
                    error = DynamoDBCommitError(error_response={}, operation_name="")
                    error.response = e.response
                    error.operation_name = e.operation_name
                    raise error from e
        await self.rollback()

    async def rollback(self) -> None:
        self.customers.session.clear()
