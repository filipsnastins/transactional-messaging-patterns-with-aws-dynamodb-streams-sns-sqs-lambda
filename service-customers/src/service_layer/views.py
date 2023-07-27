import uuid

import structlog
from service_layer.response import GetCustomerNotFoundResponse, GetCustomerResponse
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def get_customer(
    uow: AbstractUnitOfWork, customer_id: uuid.UUID
) -> GetCustomerResponse | GetCustomerNotFoundResponse:
    log = logger.bind(customer_id=customer_id)
    customer = await uow.customers.get(customer_id)
    if not customer:
        log.error("customer_not_found")
        return GetCustomerNotFoundResponse.create(customer_id)
    log.info("get_customer")
    return GetCustomerResponse.create(customer)
