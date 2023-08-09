from contextvars import ContextVar
from typing import TypedDict

import structlog
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

from adapters import clients
from adapters.settings import get_settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


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


def get_aggregate_table_name() -> str:
    return get_settings().dynamodb_aggregate_table_name


def get_outbox_table_name() -> str:
    return get_settings().dynamodb_outbox_table_name


async def create_aggregate_table() -> None:
    table_name = get_aggregate_table_name()
    async with clients.get_dynamodb_client() as client:
        try:
            await client.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {
                        "AttributeName": "PK",
                        "AttributeType": "S",
                    },
                ],
                KeySchema=[
                    {
                        "AttributeName": "PK",
                        "KeyType": "HASH",
                    },
                ],
                BillingMode="PAY_PER_REQUEST",
            )
        except client.exceptions.ResourceInUseException:
            logger.info("dynamodb_table_already_exists", table_name=table_name)
        else:
            logger.info("dynamodb_table_created", table_name=table_name)


async def create_outbox_table() -> None:
    table_name = get_outbox_table_name()
    async with clients.get_dynamodb_client() as client:
        try:
            await client.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {
                        "AttributeName": "PK",
                        "AttributeType": "S",
                    },
                ],
                KeySchema=[
                    {
                        "AttributeName": "PK",
                        "KeyType": "HASH",
                    },
                ],
                BillingMode="PAY_PER_REQUEST",
                StreamSpecification={
                    "StreamEnabled": True,
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                },
            )
        except client.exceptions.ResourceInUseException:
            logger.info("dynamodb_table_already_exists", table_name=table_name)
        else:
            logger.info("dynamodb_table_created", table_name=table_name)
