from dataclasses import dataclass
from decimal import Decimal


class Command:
    pass


@dataclass
class CreateCustomerCommand(Command):
    name: str
    credit_limit: Decimal
