from contextvars import ContextVar
from typing import TypedDict

from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef


class DynamoDBSessionItems(TypedDict):
    transact_item: TransactWriteItemTypeDef
    raise_on_condition_check_failure: Exception | None


class DynamoDBSession:
    _session: ContextVar[list[DynamoDBSessionItems]]

    def __init__(self) -> None:
        self._session = ContextVar("__dynamodb_session", default=[])

    def add(
        self, transact_item: TransactWriteItemTypeDef, raise_on_condition_check_failure: Exception | None = None
    ) -> None:
        item = DynamoDBSessionItems(
            transact_item=transact_item,
            raise_on_condition_check_failure=raise_on_condition_check_failure,
        )
        self._session.get().append(item)

    def get(self) -> list[DynamoDBSessionItems]:
        return self._session.get()

    def clear(self) -> None:
        self._session.get().clear()
