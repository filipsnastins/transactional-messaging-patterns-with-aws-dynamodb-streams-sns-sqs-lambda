import os
from contextvars import ContextVar
from typing import TypedDict

import structlog
from aiobotocore.session import get_session
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

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


def get_dynamodb_client() -> DynamoDBClient:
    session = get_session()
    return session.create_client(
        "dynamodb",
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"),
    )


def get_aggregate_table_name() -> str:
    return os.environ["DYNAMODB_AGGREGATE_TABLE_NAME"]


def get_outbox_table_name() -> str:
    return os.environ["DYNAMODB_OUTBOX_TABLE_NAME"]


async def create_aggregate_table() -> None:
    table_name = get_aggregate_table_name()
    async with get_dynamodb_client() as client:
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
    async with get_dynamodb_client() as client:
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
