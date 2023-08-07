import structlog

from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from customers.events import (
    CustomerCreditReservedEvent,
    CustomerValidationErrors,
    CustomerValidationFailedEvent,
    OrderCreatedExternalEvent,
)
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_customer(uow: AbstractUnitOfWork, cmd: CreateCustomerCommand) -> Customer:
    async with uow:
        customer, event = Customer.create(
            name=cmd.name, credit_limit=cmd.credit_limit, correlation_id=cmd.correlation_id
        )
        await uow.customers.create(customer)
        await uow.events.publish([event])
        await uow.commit()
        logger.info("customer_created", customer_id=customer.id)
        return customer


async def reserve_credit(uow: AbstractUnitOfWork, event: OrderCreatedExternalEvent) -> None:
    log = logger.bind(customer_id=event.customer_id, order_id=event.order_id, order_total=event.order_total)
    customer = await uow.customers.get(customer_id=event.customer_id)
    if not customer:
        customer_validation_failed_event = CustomerValidationFailedEvent(
            customer_id=event.customer_id,
            order_id=event.order_id,
            error=CustomerValidationErrors.CUSTOMER_NOT_FOUND,
        )
        await uow.events.publish([customer_validation_failed_event])
        await uow.commit()
        log.error("customer_not_found")
        return

    customer.reserve_credit(order_id=event.order_id, order_total=event.order_total)
    credit_reserved_event = CustomerCreditReservedEvent(customer_id=event.customer_id, order_id=event.order_id)
    await uow.events.publish([credit_reserved_event])
    await uow.commit()
    log.info("credit_reserved")
