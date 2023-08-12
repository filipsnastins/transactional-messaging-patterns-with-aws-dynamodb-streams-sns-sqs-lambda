import datetime
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum

from stockholm import Money

from customers.customer import Customer
from utils.time import datetime_to_str


class ResponseTypes(Enum):
    SUCCESS = "SUCCESS"
    CUSTOMER_NOT_FOUND_ERROR = "CUSTOMER_NOT_FOUND_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class GetCustomerLink:
    href: str

    @staticmethod
    def create(customer_id: uuid.UUID) -> "GetCustomerLink":
        return GetCustomerLink(href=f"/customer/{customer_id}")


@dataclass
class CustomerLinks:
    self: GetCustomerLink

    @staticmethod
    def create(customer_id: uuid.UUID) -> "CustomerLinks":
        return CustomerLinks(self=GetCustomerLink.create(customer_id))


@dataclass(kw_only=True)
class Response:
    type: ResponseTypes
    _links: CustomerLinks


@dataclass(kw_only=True)
class FailureResponse(Response):
    @staticmethod
    def create(type: ResponseTypes, customer_id: uuid.UUID) -> "FailureResponse":
        return FailureResponse(type=type, _links=CustomerLinks.create(customer_id))

    def to_dict(self) -> dict:
        return {
            "error": self.type.value,
            "_links": asdict(self._links),
        }


@dataclass
class GetCustomerResponse(Response):
    id: uuid.UUID
    name: str
    credit_limit: Decimal
    available_credit: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    _links: CustomerLinks

    @staticmethod
    def create(customer: Customer) -> "GetCustomerResponse":
        return GetCustomerResponse(
            type=ResponseTypes.SUCCESS,
            id=customer.id,
            name=customer.name,
            credit_limit=customer.credit_limit,
            available_credit=customer.available_credit(),
            version=customer.version,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            _links=CustomerLinks.create(customer_id=customer.id),
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


@dataclass
class CustomerCreatedResponse(Response):
    id: uuid.UUID
    _links: CustomerLinks

    @staticmethod
    def create(customer: Customer) -> "CustomerCreatedResponse":
        _links = CustomerLinks.create(customer_id=customer.id)
        return CustomerCreatedResponse(
            type=ResponseTypes.SUCCESS,
            id=customer.id,
            _links=_links,
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "_links": asdict(self._links),
        }
