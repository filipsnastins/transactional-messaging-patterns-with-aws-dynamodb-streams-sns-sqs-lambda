import uuid

from customers.customer import CustomerNotFoundError
from service_layer.response import GetCustomerResponse
from service_layer.unit_of_work import AbstractUnitOfWork


async def get_customer(uow: AbstractUnitOfWork, customer_id: uuid.UUID) -> GetCustomerResponse:
    customer = await uow.customers.get(customer_id)
    if not customer:
        raise CustomerNotFoundError(customer_id)
    return GetCustomerResponse.from_customer(customer)
