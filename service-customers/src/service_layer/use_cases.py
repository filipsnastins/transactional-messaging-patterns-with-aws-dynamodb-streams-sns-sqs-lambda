import structlog

from adapters.customer_repository import CustomerNotFoundError
from customers.commands import CreateCustomerCommand, ReleaseCreditCommand, ReserveCreditCommand
from customers.customer import Customer, CustomerCreditLimitExceededError
from customers.events import (
    CustomerCreatedEvent,
    CustomerCreditReservationFailedEvent,
    CustomerCreditReservedEvent,
    CustomerValidationErrors,
    CustomerValidationFailedEvent,
)
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_customer(uow: AbstractUnitOfWork, cmd: CreateCustomerCommand) -> Customer:
    async with uow:
        customer = Customer.create(name=cmd.name, credit_limit=cmd.credit_limit)
        event = CustomerCreatedEvent(
            correlation_id=cmd.correlation_id,
            customer_id=customer.id,
            name=customer.name,
            credit_limit=customer.credit_limit,
            created_at=customer.created_at,
        )
        await uow.customers.create(customer)
        await uow.events.publish([event])
        await uow.commit()
        logger.info("customer_created", customer_id=customer.id)
        return customer


async def reserve_credit(uow: AbstractUnitOfWork, cmd: ReserveCreditCommand) -> None:
    log = logger.bind(customer_id=cmd.customer_id, order_id=cmd.order_id, order_total=cmd.order_total)
    customer = await uow.customers.get(customer_id=cmd.customer_id)
    if not customer:
        await uow.events.publish(
            [
                CustomerValidationFailedEvent(
                    correlation_id=cmd.correlation_id,
                    customer_id=cmd.customer_id,
                    order_id=cmd.order_id,
                    error=CustomerValidationErrors.CUSTOMER_NOT_FOUND,
                )
            ]
        )
        await uow.commit()
        log.error("customer_not_found")
        return

    try:
        customer.reserve_credit(order_id=cmd.order_id, order_total=cmd.order_total)
        await uow.customers.update(customer)
        await uow.events.publish(
            [
                CustomerCreditReservedEvent(
                    correlation_id=cmd.correlation_id, customer_id=cmd.customer_id, order_id=cmd.order_id
                )
            ]
        )
        await uow.commit()
        log.info("credit_reserved")
    except CustomerCreditLimitExceededError:
        await uow.events.publish(
            [
                CustomerCreditReservationFailedEvent(
                    correlation_id=cmd.correlation_id, customer_id=cmd.customer_id, order_id=cmd.order_id
                )
            ]
        )
        await uow.commit()
        log.info("credit_limit_exceeded")


async def release_credit(uow: AbstractUnitOfWork, cmd: ReleaseCreditCommand) -> None:
    log = logger.bind(customer_id=cmd.customer_id, order_id=cmd.order_id)
    customer = await uow.customers.get(customer_id=cmd.customer_id)
    if not customer:
        raise CustomerNotFoundError(cmd.customer_id)

    customer.release_credit(order_id=cmd.order_id)
    await uow.customers.update(customer)
    await uow.commit()
    log.info("credit_released")
