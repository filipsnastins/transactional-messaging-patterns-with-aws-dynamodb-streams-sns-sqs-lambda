import structlog

from adapters.order_repository import OrderNotFoundError
from orders.commands import ApproveOrderCommand, CreateOrderCommand
from orders.events import OrderApprovedEvent, OrderCreatedEvent
from orders.order import Order
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_order(uow: AbstractUnitOfWork, cmd: CreateOrderCommand) -> Order:
    order = Order.create(customer_id=cmd.customer_id, order_total=cmd.order_total)
    event = OrderCreatedEvent(
        correlation_id=cmd.correlation_id,
        order_id=order.id,
        customer_id=order.customer_id,
        state=order.state,
        order_total=order.order_total,
        created_at=order.created_at,
    )

    await uow.orders.create(order)
    await uow.events.publish([event])
    await uow.commit()
    logger.info("order_created", order_id=order.id, customer_id=order.customer_id)
    return order


async def approve_order(uow: AbstractUnitOfWork, cmd: ApproveOrderCommand) -> None:
    log = logger.bind(order_id=cmd.order_id)
    order = await uow.orders.get(order_id=cmd.order_id)
    if not order:
        log.error("order_not_found")
        raise OrderNotFoundError(cmd.order_id)

    order.note_credit_reserved()
    event = OrderApprovedEvent(
        correlation_id=cmd.correlation_id,
        order_id=order.id,
        customer_id=order.customer_id,
        state=order.state,
    )

    await uow.orders.update(order)
    await uow.events.publish([event])
    await uow.commit()
    log.error("order_approved", customer_id=order.customer_id)
