import uuid

import structlog

from service_layer.response import FailureResponse, GetCustomerResponse, ResponseTypes
from service_layer.unit_of_work import UnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def get_customer(uow: UnitOfWork, customer_id: uuid.UUID) -> GetCustomerResponse | FailureResponse:
    log = logger.bind(customer_id=customer_id)
    customer = await uow.customers.get(customer_id)
    if not customer:
        log.error("customer_not_found")
        return FailureResponse.create(ResponseTypes.CUSTOMER_NOT_FOUND_ERROR, customer_id=customer_id)
    log.info("get_customer")
    return GetCustomerResponse.create(customer)
