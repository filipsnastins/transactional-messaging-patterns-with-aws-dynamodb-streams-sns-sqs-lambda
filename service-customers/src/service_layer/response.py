from dataclasses import dataclass

from customers.customer import Customer


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
            "_links": {
                "self": {"href": self._links.self.href},
            },
        }
