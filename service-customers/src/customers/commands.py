import uuid
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(kw_only=True)
class Command:
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(kw_only=True)
class CreateCustomerCommand(Command):
    name: str
    credit_limit: Decimal
