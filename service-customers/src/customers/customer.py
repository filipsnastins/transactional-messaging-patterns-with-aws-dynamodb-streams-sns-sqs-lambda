import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal

from stockholm import Money

from customers.events import CustomerCreatedEvent, Event


class CustomerCreditLimitExceededError(Exception):
    pass


@dataclass
class Customer:
    id: uuid.UUID
    name: str
    credit_limit: Decimal
    credit_reservations: dict[uuid.UUID, Decimal]
    created_at: datetime.datetime
    version: int
    events: list[Event]

    def __init__(
        self,
        name: str,
        credit_limit: Decimal,
        id: uuid.UUID,
        credit_reservations: dict[uuid.UUID, Decimal],
        created_at: datetime.datetime,
        version: int,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.name = name
        self.credit_limit = credit_limit
        self.credit_reservations = credit_reservations
        self.created_at = created_at
        self.version = version
        self.events = []

    @staticmethod
    def create(name: str, credit_limit: Decimal, correlation_id: uuid.UUID) -> "Customer":
        customer = Customer(
            id=uuid.uuid4(),
            name=name,
            credit_limit=credit_limit,
            credit_reservations={},
            created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
            version=0,
        )
        event = CustomerCreatedEvent(
            customer_id=customer.id,
            correlation_id=correlation_id,
            name=customer.name,
            credit_limit=customer.credit_limit,
            created_at=customer.created_at,
        )
        customer.events.append(event)
        return customer

    @staticmethod
    def from_dict(data: dict) -> "Customer":
        return Customer(**data)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "credit_limit": int(Money(self.credit_limit).to_sub_units()),
            "credit_reservations": self.credit_reservations,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }

    def available_credit(self) -> Decimal:
        return self.credit_limit - sum(self.credit_reservations.values())

    def reserve_credit(self, id: uuid.UUID, order_total: Decimal) -> None:
        if self.available_credit() >= order_total:
            self.credit_reservations[id] = order_total
        else:
            raise CustomerCreditLimitExceededError

    def unreserve_credit(self, id: uuid.UUID) -> None:
        self.credit_reservations.pop(id)
