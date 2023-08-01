import structlog

from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_customer(uow: AbstractUnitOfWork, cmd: CreateCustomerCommand) -> Customer:
    async with uow:
        customer = Customer.create(name=cmd.name, credit_limit=cmd.credit_limit, correlation_id=cmd.correlation_id)
        await uow.customers.create(customer)
        await uow.events.publish(customer.events)
        await uow.commit()
        logger.info("customer_created", customer_id=customer.id)
        return customer
