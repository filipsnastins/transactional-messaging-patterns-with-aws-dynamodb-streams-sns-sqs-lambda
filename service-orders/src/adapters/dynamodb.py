import structlog

from adapters import clients
from adapters.settings import get_settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


def get_orders_table_name() -> str:
    return get_settings().dynamodb_orders_table_name


async def create_orders_table() -> None:
    table_name = get_orders_table_name()
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
            logger.info("orders_dynamodb_table_already_exists", table_name=table_name)
        else:
            logger.info("orders_dynamodb_table_created", table_name=table_name)
