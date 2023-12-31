import uuid

import structlog

from service_layer.response import FailureResponse, GetOrderResponse, ResponseTypes
from service_layer.unit_of_work import UnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def get_order(uow: UnitOfWork, order_id: uuid.UUID) -> GetOrderResponse | FailureResponse:
    log = logger.bind(order_id=order_id)
    order = await uow.orders.get(order_id)
    if not order:
        log.error("order_not_found")
        return FailureResponse.create(ResponseTypes.ORDER_NOT_FOUND_ERROR, order_id=order_id)
    log.info("get_order")
    return GetOrderResponse.create(order)
