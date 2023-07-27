import datetime
from dataclasses import asdict, dataclass
from decimal import Decimal

from customers.customer import Customer
from stockholm import Money


@dataclass
class Href:
    href: str


@dataclass
class CreateCustomerResponseLinks:
    self: Href

    @staticmethod
    def from_customer(customer: Customer) -> "CreateCustomerResponseLinks":
        return CreateCustomerResponseLinks(self=Href(href=f"/customer/{customer.id}"))


@dataclass
class CreateCustomerResponse:
    id: str
    _links: CreateCustomerResponseLinks

    @staticmethod
    def from_customer(customer: Customer) -> "CreateCustomerResponse":
        _links = CreateCustomerResponseLinks.from_customer(customer)
        return CreateCustomerResponse(id=str(customer.id), _links=_links)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "_links": asdict(self._links),
        }


@dataclass
class GetCustomerResponseLinks:
    self: Href

    @staticmethod
    def from_customer(customer: Customer) -> "GetCustomerResponseLinks":
        return GetCustomerResponseLinks(self=Href(href=f"/customer/{customer.id}"))


@dataclass
class GetCustomerResponse:
    id: str
    name: str
    credit_limit: Decimal
    available_credit: Decimal
    created_at: datetime.datetime
    version: int
    _links: GetCustomerResponseLinks

    @staticmethod
    def from_customer(customer: Customer) -> "GetCustomerResponse":
        return GetCustomerResponse(
            id=str(customer.id),
            name=customer.name,
            credit_limit=customer.credit_limit,
            available_credit=customer.available_credit(),
            created_at=customer.created_at,
            version=customer.version,
            _links=GetCustomerResponseLinks.from_customer(customer),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "credit_limit": int(Money(self.credit_limit).to_sub_units()),
            "available_credit": int(Money(self.available_credit).to_sub_units()),
            "created_at": self.created_at.isoformat(),
            "version": self.version,
            "_links": asdict(self._links),
        }
