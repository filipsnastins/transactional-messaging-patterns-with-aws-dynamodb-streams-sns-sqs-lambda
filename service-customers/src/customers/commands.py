from dataclasses import dataclass
from decimal import Decimal

from stockholm import Money


class Command:
    pass


@dataclass
class CreateCustomerCommand(Command):
    name: str
    credit_limit: Decimal

    @staticmethod
    def from_dict(data: dict) -> "CreateCustomerCommand":
        return CreateCustomerCommand(
            name=str(data["name"]),
            credit_limit=Money.from_sub_units(int(data["credit_limit"])).as_decimal(),
        )
