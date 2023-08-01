import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from stockholm import Money


@dataclass(kw_only=True)
class Command:
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(kw_only=True)
class CreateCustomerCommand(Command):
    name: str
    credit_limit: Decimal

    @staticmethod
    def from_dict(data: dict) -> "CreateCustomerCommand":
        return CreateCustomerCommand(
            name=str(data["name"]),
            credit_limit=Money.from_sub_units(int(data["credit_limit"])).as_decimal(),
        )
