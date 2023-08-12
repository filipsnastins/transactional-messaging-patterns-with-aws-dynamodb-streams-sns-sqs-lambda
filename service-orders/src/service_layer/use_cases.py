import structlog

from adapters.order_repository import OrderAlreadyExistsError, OrderNotFoundError
from orders.commands import ApproveOrderCommand, CancelOrderCommand, CreateOrderCommand, RejectOrderCommand
from orders.events import OrderApprovedEvent, OrderCancelledEvent, OrderCreatedEvent, OrderRejectedEvent
from orders.order import Order, OrderAlreadyCancelledError, PendingOrderCannotBeCancelledError
from service_layer.response import FailureResponse, OrderCancelledResponse, OrderCreatedResponse, ResponseTypes
from service_layer.unit_of_work import UnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_order(uow: UnitOfWork, cmd: CreateOrderCommand) -> OrderCreatedResponse | FailureResponse:
    order = Order.create(customer_id=cmd.customer_id, order_total=cmd.order_total)
    event = OrderCreatedEvent(
        correlation_id=cmd.correlation_id,
        order_id=order.id,
        customer_id=order.customer_id,
        state=order.state,
        order_total=order.order_total,
        created_at=order.created_at,
    )

    log = logger.bind(order_id=order.id, customer_id=order.customer_id)
    try:
        await uow.orders.create(order)
        await uow.events.publish([event])
        await uow.commit()
    except OrderAlreadyExistsError:
        log.error("order_already_exists", customer_id=order.customer_id)
        return FailureResponse.create(ResponseTypes.ORDER_ALREADY_EXISTS_ERROR, order_id=order.id)

    log.info("order_created", order_id=order.id, customer_id=order.customer_id)
    return OrderCreatedResponse.create(order)


async def approve_order(uow: UnitOfWork, cmd: ApproveOrderCommand) -> None:
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
    log.info("order_approved", customer_id=order.customer_id)


async def reject_order(uow: UnitOfWork, cmd: RejectOrderCommand) -> None:
    log = logger.bind(order_id=cmd.order_id)
    order = await uow.orders.get(order_id=cmd.order_id)
    if not order:
        log.error("order_not_found")
        raise OrderNotFoundError(cmd.order_id)

    order.note_credit_rejected()
    event = OrderRejectedEvent(
        correlation_id=cmd.correlation_id,
        order_id=order.id,
        customer_id=order.customer_id,
        state=order.state,
    )

    await uow.orders.update(order)
    await uow.events.publish([event])
    await uow.commit()
    log.info("order_rejected", customer_id=order.customer_id)


async def cancel_order(uow: UnitOfWork, cmd: CancelOrderCommand) -> OrderCancelledResponse | FailureResponse:
    order = await uow.orders.get(order_id=cmd.order_id)
    if not order:
        logger.error("order_not_found", order_id=cmd.order_id)
        return FailureResponse.create(ResponseTypes.ORDER_NOT_FOUND_ERROR, order_id=cmd.order_id)

    log = logger.bind(order_id=cmd.order_id, customer_id=order.customer_id)
    try:
        order.cancel()
    except PendingOrderCannotBeCancelledError:
        log.error("pending_order_cannot_be_cancelled")
        return FailureResponse.create(ResponseTypes.PENDING_ORDER_CANNOT_BE_CANCELLED_ERROR, order_id=cmd.order_id)
    except OrderAlreadyCancelledError:
        log.warning("order_already_cancelled")
        return OrderCancelledResponse.create(order)

    event = OrderCancelledEvent(
        correlation_id=cmd.correlation_id,
        order_id=order.id,
        customer_id=order.customer_id,
        state=order.state,
    )
    await uow.orders.update(order)
    await uow.events.publish([event])
    await uow.commit()
    log.info("order_cancelled")
    return OrderCancelledResponse.create(order)
