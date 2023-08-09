import datetime
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol

from stockholm import Money

from customers.customer import Customer
from utils.time import datetime_to_str


class Response(Protocol):
    @property
    def status_code(self) -> int:
        ...


class ErrorCodes(Enum):
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"


class ErrorResponse(Response, Protocol):
    error: ErrorCodes


@dataclass
class CustomerLink:
    href: str

    @staticmethod
    def create(customer_id: uuid.UUID) -> "CustomerLink":
        return CustomerLink(href=f"/customer/{str(customer_id)}")


@dataclass
class SelfCustomerLink:
    self: CustomerLink

    @staticmethod
    def create(customer_id: uuid.UUID) -> "SelfCustomerLink":
        return SelfCustomerLink(self=CustomerLink.create(customer_id))


@dataclass
class CreateCustomerResponse(Response):
    id: uuid.UUID
    _links: SelfCustomerLink

    @staticmethod
    def create(customer: Customer) -> "CreateCustomerResponse":
        _links = SelfCustomerLink.create(customer_id=customer.id)
        return CreateCustomerResponse(id=customer.id, _links=_links)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "_links": asdict(self._links),
        }

    @property
    def status_code(self) -> int:
        return 200


@dataclass
class GetCustomerResponse(Response):
    id: uuid.UUID
    name: str
    credit_limit: Decimal
    available_credit: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    _links: SelfCustomerLink

    @staticmethod
    def create(customer: Customer) -> "GetCustomerResponse":
        return GetCustomerResponse(
            id=customer.id,
            name=customer.name,
            credit_limit=customer.credit_limit,
            available_credit=customer.available_credit(),
            version=customer.version,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            _links=SelfCustomerLink.create(customer_id=customer.id),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "credit_limit": int(Money(self.credit_limit).to_sub_units()),
            "available_credit": int(Money(self.available_credit).to_sub_units()),
            "version": self.version,
            "created_at": datetime_to_str(self.created_at),
            "updated_at": datetime_to_str(self.updated_at) if self.updated_at else None,
            "_links": asdict(self._links),
        }

    @property
    def status_code(self) -> int:
        return 200


@dataclass
class CustomerNotFoundResponse(ErrorResponse):
    _links: SelfCustomerLink
    error: ErrorCodes = ErrorCodes.CUSTOMER_NOT_FOUND

    @staticmethod
    def create(customer_id: uuid.UUID) -> "CustomerNotFoundResponse":
        return CustomerNotFoundResponse(_links=SelfCustomerLink.create(customer_id))

    def to_dict(self) -> dict:
        return {
            "error": self.error.value,
            "_links": asdict(self._links),
        }

    @property
    def status_code(self) -> int:
        return 404
