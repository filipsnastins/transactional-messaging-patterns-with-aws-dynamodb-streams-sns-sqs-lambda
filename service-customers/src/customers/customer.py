import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal

from stockholm import Money

from utils.time import datetime_to_str, utcnow


class OptimisticLockError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class CustomerAlreadyExistsError(Exception):
    pass


class CustomerCreditLimitExceededError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


@dataclass
class Customer:
    id: uuid.UUID
    name: str
    credit_limit: Decimal
    credit_reservations: dict[uuid.UUID, Decimal]
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    version: int

    def __init__(
        self,
        name: str,
        credit_limit: Decimal,
        id: uuid.UUID,
        credit_reservations: dict[uuid.UUID, Decimal],
        version: int,
        created_at: datetime.datetime,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.name = name
        self.credit_limit = credit_limit
        self.credit_reservations = credit_reservations
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(name: str, credit_limit: Decimal) -> "Customer":
        return Customer(
            id=uuid.uuid4(),
            name=name,
            credit_limit=credit_limit,
            credit_reservations={},
            version=0,
            created_at=utcnow(),
            updated_at=None,
        )

    @staticmethod
    def from_dict(data: dict) -> "Customer":
        return Customer(**data)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "credit_limit": int(Money(self.credit_limit).to_sub_units()),
            "credit_reservations": self.credit_reservations,
            "version": self.version,
            "created_at": datetime_to_str(self.created_at),
            "updated_at": datetime_to_str(self.updated_at) if self.updated_at else None,
        }

    def available_credit(self) -> Decimal:
        return self.credit_limit - sum(self.credit_reservations.values())

    def reserve_credit(self, order_id: uuid.UUID, order_total: Decimal) -> None:
        if self.available_credit() >= order_total:
            self.credit_reservations[order_id] = order_total
        else:
            raise CustomerCreditLimitExceededError(self.id)

    def release_credit(self, order_id: uuid.UUID) -> None:
        try:
            self.credit_reservations.pop(order_id)
        except KeyError as e:
            raise OrderNotFoundError(order_id) from e
