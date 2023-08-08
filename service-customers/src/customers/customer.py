import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal

from utils.time import utcnow


class CustomerCreditLimitExceededError(Exception):
    pass


class CreditNotReservedForOrderError(Exception):
    pass


@dataclass
class Customer:
    id: uuid.UUID
    name: str
    credit_limit: Decimal
    credit_reservations: dict[uuid.UUID, Decimal]
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    def __init__(
        self,
        id: uuid.UUID,
        name: str,
        credit_limit: Decimal,
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
            raise CreditNotReservedForOrderError(order_id) from e
