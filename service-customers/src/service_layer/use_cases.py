import structlog
from adapters.publisher import publish
from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from service_layer.unit_of_work import AbstractUnitOfWork
from structlog import get_logger

logger: structlog.stdlib.BoundLogger = get_logger()


async def create_customer(uow: AbstractUnitOfWork, cmd: CreateCustomerCommand) -> Customer:
    async with uow:
        customer = Customer.create(name=cmd.name, credit_limit=cmd.credit_limit)
        await uow.customers.create(customer)
        await publish(customer.events)
        await uow.commit()
        logger.info("customer_created", customer_id=customer.id)
        return customer
