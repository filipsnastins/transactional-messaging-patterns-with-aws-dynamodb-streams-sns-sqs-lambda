import datetime
import uuid
from contextvars import ContextVar
from decimal import Decimal
from typing import Protocol, TypedDict, TypeVar

from adapters import dynamodb
from customers.customer import Customer
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

ModelType = TypeVar("ModelType")


class CustomerAlreadyExistsError(Exception):
    pass


class DynamoDBSessionItems(TypedDict):
    transact_item: TransactWriteItemTypeDef
    raise_on_condition_check_failure: Exception | None


class DynamoDBSession:
    _session: ContextVar[list[DynamoDBSessionItems]]

    def __init__(self) -> None:
        self._session = ContextVar("service_layer.unit_of_work.dynamodb_session.session", default=[])

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


class AbstractRepository(Protocol):
    async def create(self, customer: Customer) -> None:
        ...

    async def get(self, customer_id: uuid.UUID) -> Customer | None:
        ...


class DynamoDBRepository(AbstractRepository):
    def __init__(self, session: DynamoDBSession) -> None:
        self.session = session

    async def create(self, customer: Customer) -> None:
        self.session.add(
            {
                "ConditionCheck": {
                    "TableName": dynamodb.get_table_name(),
                    "Key": {"PK": {"S": f"CUSTOMER#{customer.id}"}},
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            raise_on_condition_check_failure=CustomerAlreadyExistsError(customer.id),
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

    async def get(self, customer_id: uuid.UUID) -> Customer | None:
        async with dynamodb.get_dynamodb_client() as client:
            response = await client.get_item(
                TableName=dynamodb.get_table_name(),
                Key={"PK": {"S": f"CUSTOMER#{customer_id}"}},
            )
            item = response.get("Item")
            if not item:
                return None
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
