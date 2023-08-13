from contextvars import ContextVar
from typing import TypedDict

from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

from unit_of_work.dynamodb.client import DynamoDBClientFactory


class DynamoDBSessionItems(TypedDict):
    transact_item: TransactWriteItemTypeDef
    raise_on_condition_check_failure: Exception | None


class DynamoDBSession:
    _session: ContextVar[list[DynamoDBSessionItems]]

    def __init__(self, client_factory: DynamoDBClientFactory) -> None:
        self.get_client = client_factory
        self._session = ContextVar("__unit_of_work.dynamodb.session", default=[])

    def add(
        self, transact_item: TransactWriteItemTypeDef, raise_on_condition_check_failure: Exception | None = None
    ) -> None:
        item = DynamoDBSessionItems(
            transact_item=transact_item,
            raise_on_condition_check_failure=raise_on_condition_check_failure,
        )
        self._session.get().append(item)

    async def commit(self) -> None:
        items = self._session.get()
        if not items:
            return
        async with self.get_client() as client:
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
                self.rollback()

    def rollback(self) -> None:
        self._session.get().clear()
