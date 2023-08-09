import uuid

import structlog

from service_layer.response import GetOrderResponse, OrderNotFoundResponse
from service_layer.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def get_order(uow: AbstractUnitOfWork, order_id: uuid.UUID) -> GetOrderResponse | OrderNotFoundResponse:
    log = logger.bind(order_id=order_id)
    order = await uow.orders.get(order_id)
    if not order:
        log.error("order_not_found")
        return OrderNotFoundResponse.create(order_id)
    log.info("get_order")
    return GetOrderResponse.create(order)
