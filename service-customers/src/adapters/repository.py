import datetime
import uuid
from contextvars import ContextVar
from decimal import Decimal
from typing import Generic, Protocol, TypeVar

from adapters import dynamodb
from customers.customer import Customer
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

ModelType = TypeVar("ModelType")


class CustomerNotFoundError(Exception):
    pass


class Session(Protocol, Generic[ModelType]):
    def add(self, instance: ModelType) -> None:
        ...

    def get(self) -> list[ModelType]:
        ...

    def clear(self) -> None:
        ...


class DynamoDBSession(Session[TransactWriteItemTypeDef]):
    _session: ContextVar[list[TransactWriteItemTypeDef]]

    def __init__(self) -> None:
        self._session = ContextVar("session", default=[])

    def add(self, instance: TransactWriteItemTypeDef) -> None:
        self._session.get().append(instance)

    def get(self) -> list[TransactWriteItemTypeDef]:
        return self._session.get()

    def clear(self) -> None:
        return self._session.get().clear()


class AbstractCustomersRepository(Protocol, Generic[ModelType]):
    session: Session[ModelType]

    async def create(self, customer: Customer) -> None:
        ...

    async def get(self, customer_id: uuid.UUID) -> Customer:
        ...


class DynamoDBCustomersRepository(AbstractCustomersRepository[TransactWriteItemTypeDef]):
    def __init__(self) -> None:
        self.session = DynamoDBSession()

    async def create(self, customer: Customer) -> None:
        self.session.add(
            {
                "ConditionCheck": {
                    "TableName": dynamodb.get_table_name(),
                    "Key": {"PK": {"S": f"CUSTOMER#{customer.id}"}},
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
        )
        self.session.add(
            {
                "Put": {
                    "TableName": dynamodb.get_table_name(),
                    "Item": {
                        "PK": {"S": f"CUSTOMER#{customer.id}"},
                        "Id": {"S": str(customer.id)},
                        "Name": {"S": customer.name},
                        "CreditLimit": {"N": str(customer.credit_limit)},
                        "CreditReservations": {
                            "M": {
                                str(order_id): {"N": str(order_total)}
                                for order_id, order_total in customer.credit_reservations.items()
                            }
                        },
                        "CreatedAt": {"S": customer.created_at.isoformat()},
                        "Version": {"N": str(customer.version)},
                    },
                }
            }
        )

    async def get(self, customer_id: uuid.UUID) -> Customer:
        async with dynamodb.get_dynamodb_client() as client:
            response = await client.get_item(
                TableName=dynamodb.get_table_name(),
                Key={"PK": {"S": f"CUSTOMER#{customer_id}"}},
            )
            item = response.get("Item")
            if not item:
                raise CustomerNotFoundError(customer_id)
            return Customer(
                id=uuid.UUID(item["Id"]["S"]),
                name=item["Name"]["S"],
                credit_limit=Decimal(item["CreditLimit"]["N"]),
                credit_reservations={
                    uuid.UUID(order_id): order_total["N"]
                    for order_id, order_total in item["CreditReservations"]["M"].items()
                },
                created_at=datetime.datetime.fromisoformat(item["CreatedAt"]["S"]),
                version=int(item["Version"]["N"]),
            )
