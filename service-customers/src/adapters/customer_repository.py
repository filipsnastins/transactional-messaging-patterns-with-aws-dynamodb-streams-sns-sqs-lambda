import uuid
from typing import Protocol

import structlog
from stockholm import Money
from unit_of_work.dynamodb import DynamoDBSession

from customers.customer import Customer
from utils.time import datetime_to_str, str_to_datetime, utcnow

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class OptimisticLockError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class CustomerAlreadyExistsError(Exception):
    pass


class CustomerRepository(Protocol):
    async def create(self, customer: Customer) -> None:
        ...

    async def update(self, customer: Customer) -> None:
        ...

    async def get(self, customer_id: uuid.UUID) -> Customer | None:
        ...


class DynamoDBCustomerRepository(CustomerRepository):
    def __init__(self, table_name: str, session: DynamoDBSession) -> None:
        self._table_name = table_name
        self._session = session

    async def create(self, customer: Customer) -> None:
        self._session.add(
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        "PK": {"S": f"CUSTOMER#{customer.id}"},
                        "CustomerId": {"S": str(customer.id)},
                        "Name": {"S": customer.name},
                        "CreditLimit": {"N": str(Money(customer.credit_limit).to_sub_units())},
                        "CreditReservations": {
                            "M": {
                                str(order_id): {"N": str(Money(order_total).to_sub_units())}
                                for order_id, order_total in customer.credit_reservations.items()
                            }
                        },
                        "Version": {"N": str(customer.version)},
                        "CreatedAt": {"S": datetime_to_str(customer.created_at)},
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            raise_on_condition_check_failure=CustomerAlreadyExistsError(customer.id),
        )
        logger.info("dynamodb_customer_repository__create", customer_id=customer.id)

    async def update(self, customer: Customer) -> None:
        self._session.add(
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        "PK": {"S": f"CUSTOMER#{customer.id}"},
                        "CustomerId": {"S": str(customer.id)},
                        "Name": {"S": customer.name},
                        "CreditLimit": {"N": str(Money(customer.credit_limit).to_sub_units())},
                        "CreditReservations": {
                            "M": {
                                str(order_id): {"N": str(Money(order_total).to_sub_units())}
                                for order_id, order_total in customer.credit_reservations.items()
                            }
                        },
                        "Version": {"N": str(customer.version + 1)},
                        "CreatedAt": {"S": datetime_to_str(customer.created_at)},
                        "UpdatedAt": {"S": datetime_to_str(utcnow())},
                    },
                    "ConditionExpression": "Version = :version",
                    "ExpressionAttributeValues": {":version": {"N": str(customer.version)}},
                }
            },
            raise_on_condition_check_failure=OptimisticLockError(),
        )
        logger.info("dynamodb_customer_repository__update", customer_id=customer.id)

    async def get(self, customer_id: uuid.UUID) -> Customer | None:
        async with self._session.get_client() as client:
            response = await client.get_item(TableName=self._table_name, Key={"PK": {"S": f"CUSTOMER#{customer_id}"}})
            item = response.get("Item")
            if not item:
                logger.info(
                    "dynamodb_customer_repository__customer_not_found",
                    customer_id=customer_id,
                )
                return None
            return Customer(
                id=uuid.UUID(item["CustomerId"]["S"]),
                name=item["Name"]["S"],
                credit_limit=Money.from_sub_units(item["CreditLimit"]["N"]).as_decimal(),
                credit_reservations={
                    uuid.UUID(order_id): Money.from_sub_units(order_total["N"]).as_decimal()
                    for order_id, order_total in item["CreditReservations"]["M"].items()
                },
                version=int(item["Version"]["N"]),
                created_at=str_to_datetime(item["CreatedAt"]["S"]),
                updated_at=str_to_datetime(item["UpdatedAt"]["S"]) if item.get("UpdatedAt") else None,
            )
