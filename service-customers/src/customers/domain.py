import dataclasses
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Customer:
    customer_id: uuid.UUID
    name: str
    credit_limit: Decimal
    credit_reservations: dict[uuid.UUID, Decimal]
    created_at: datetime
    version: int

    @staticmethod
    def from_dict(data: dict) -> "Customer":
        return Customer(**data)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
