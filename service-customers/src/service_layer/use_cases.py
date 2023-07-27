from decimal import Decimal

import structlog
from customers.customer import Customer
from service_layer.unit_of_work import AbstractUnitOfWork
from structlog import get_logger

logger: structlog.stdlib.BoundLogger = get_logger()


async def create_customer(uow: AbstractUnitOfWork, name: str, credit_limit: Decimal) -> Customer:
    customer = Customer.create(name=name, credit_limit=credit_limit)
    await uow.customers.create(customer)
    await uow.commit()
    logger.info("customer_created", customer_id=customer.id)
    return customer
