import uuid
from typing import Protocol

import structlog
from stockholm import Money
from tomodachi_outbox.dynamodb import DynamoDBClientFactory, DynamoDBSession

from orders.order import Order, OrderState
from utils.time import datetime_to_str, str_to_datetime, utcnow

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class OptimisticLockError(Exception):
    pass


class OrderAlreadyExistsError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderRepository(Protocol):
    async def create(self, order: Order) -> None:
        ...

    async def get(self, order_id: uuid.UUID) -> Order | None:
        ...

    async def update(self, order: Order) -> None:
        ...


class DynamoDBOrderRepository(OrderRepository):
    def __init__(self, table_name: str, session: DynamoDBSession, client_factory: DynamoDBClientFactory) -> None:
        self.table_name = table_name
        self.session = session
        self.get_client = client_factory

    async def create(self, order: Order) -> None:
        self.session.add(
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": {
                        "PK": {"S": f"ORDER#{order.id}"},
                        "OrderId": {"S": str(order.id)},
                        "CustomerId": {"S": str(order.customer_id)},
                        "State": {"S": order.state.value},
                        "TotalAmount": {"N": str(Money(order.order_total).to_sub_units())},
                        "Version": {"N": str(order.version)},
                        "CreatedAt": {"S": datetime_to_str(order.created_at)},
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            raise_on_condition_check_failure=OrderAlreadyExistsError(order.id),
        )
        logger.info("dynamodb_order_repository__create", order_id=order.id)

    async def get(self, order_id: uuid.UUID) -> Order | None:
        async with self.get_client() as client:
            response = await client.get_item(TableName=self.table_name, Key={"PK": {"S": f"ORDER#{order_id}"}})
            item = response.get("Item")
            if not item:
                logger.debug("dynamodb_order_repository__order_not_found", order_id=order_id)
                return None
            return Order(
                id=uuid.UUID(item["OrderId"]["S"]),
                customer_id=uuid.UUID(item["CustomerId"]["S"]),
                state=OrderState[item["State"]["S"]],
                order_total=Money.from_sub_units(item["TotalAmount"]["N"]).as_decimal(),
                version=int(item["Version"]["N"]),
                created_at=str_to_datetime(item["CreatedAt"]["S"]),
                updated_at=str_to_datetime(item["UpdatedAt"]["S"]) if item.get("UpdatedAt") else None,
            )

    async def update(self, order: Order) -> None:
        self.session.add(
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": {
                        "PK": {"S": f"ORDER#{order.id}"},
                        "OrderId": {"S": str(order.id)},
                        "CustomerId": {"S": str(order.customer_id)},
                        "State": {"S": order.state.value},
                        "TotalAmount": {"N": str(Money(order.order_total).to_sub_units())},
                        "Version": {"N": str(order.version + 1)},
                        "CreatedAt": {"S": datetime_to_str(order.created_at)},
                        "UpdatedAt": {"S": datetime_to_str(utcnow())},
                    },
                    "ConditionExpression": "Version = :version",
                    "ExpressionAttributeValues": {":version": {"N": str(order.version)}},
                },
            },
            raise_on_condition_check_failure=OptimisticLockError(),
        )
