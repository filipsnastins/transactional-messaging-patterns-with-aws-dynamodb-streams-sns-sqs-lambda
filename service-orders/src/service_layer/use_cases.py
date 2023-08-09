import structlog

from orders.commands import CreateOrderCommand
from orders.order import Order
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_order(uow: AbstractUnitOfWork, cmd: CreateOrderCommand) -> Order:
    order = Order.create(customer_id=cmd.customer_id, total_amount=cmd.total_amount)
    await uow.orders.create(order)
    await uow.commit()
    logger.info("order_created", order_id=order.id, customer_id=order.customer_id)
    return order
