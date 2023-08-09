import structlog

from orders.commands import CreateOrderCommand
from orders.events import OrderCreatedEvent
from orders.order import Order
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_order(uow: AbstractUnitOfWork, cmd: CreateOrderCommand) -> Order:
    order = Order.create(customer_id=cmd.customer_id, total_amount=cmd.total_amount)
    event = OrderCreatedEvent(
        correlation_id=cmd.correlation_id,
        order_id=order.id,
        customer_id=order.customer_id,
        total_amount=order.total_amount,
        created_at=order.created_at,
    )
    await uow.orders.create(order)
    await uow.events.publish([event])
    await uow.commit()
    logger.info("order_created", order_id=order.id, customer_id=order.customer_id)
    return order
