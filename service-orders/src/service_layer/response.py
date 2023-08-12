import datetime
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum

from stockholm import Money

from orders.order import Order, OrderState
from utils.time import datetime_to_str


class ResponseTypes(Enum):
    SUCCESS = "SUCCESS"
    ORDER_NOT_FOUND_ERROR = "ORDER_NOT_FOUND_ERROR"
    ORDER_ALREADY_EXISTS_ERROR = "ORDER_ALREADY_EXISTS_ERROR"
    PENDING_ORDER_CANNOT_BE_CANCELLED_ERROR = "PENDING_ORDER_CANNOT_BE_CANCELLED_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class GetOrderLink:
    href: str

    @staticmethod
    def create(order_id: uuid.UUID) -> "GetOrderLink":
        return GetOrderLink(href=f"/order/{order_id}")


@dataclass
class CancelOrderLink:
    href: str

    @staticmethod
    def create(order_id: uuid.UUID) -> "CancelOrderLink":
        return CancelOrderLink(href=f"/order/{order_id}/cancel")


@dataclass
class OrderLinks:
    self: GetOrderLink
    cancel: CancelOrderLink

    @staticmethod
    def create(order_id: uuid.UUID) -> "OrderLinks":
        return OrderLinks(self=GetOrderLink.create(order_id), cancel=CancelOrderLink.create(order_id))


@dataclass(kw_only=True)
class Response:
    type: ResponseTypes
    _links: OrderLinks


@dataclass(kw_only=True)
class FailureResponse(Response):
    @staticmethod
    def create(type: ResponseTypes, order_id: uuid.UUID) -> "FailureResponse":
        return FailureResponse(type=type, _links=OrderLinks.create(order_id))

    def to_dict(self) -> dict:
        return {
            "error": self.type.value,
            "_links": asdict(self._links),
        }


@dataclass(kw_only=True)
class GetOrderResponse(Response):
    id: uuid.UUID
    customer_id: uuid.UUID
    state: OrderState
    order_total: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    @staticmethod
    def create(order: Order) -> "GetOrderResponse":
        return GetOrderResponse(
            type=ResponseTypes.SUCCESS,
            id=order.id,
            customer_id=order.customer_id,
            state=order.state,
            order_total=order.order_total,
            version=order.version,
            created_at=order.created_at,
            updated_at=order.updated_at,
            _links=OrderLinks.create(order_id=order.id),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "state": self.state.value,
            "order_total": int(Money(self.order_total).to_sub_units()),
            "version": self.version,
            "created_at": datetime_to_str(self.created_at),
            "updated_at": datetime_to_str(self.updated_at) if self.updated_at else None,
            "_links": asdict(self._links),
        }


@dataclass(kw_only=True)
class OrderCreatedResponse(Response):
    id: uuid.UUID

    @staticmethod
    def create(order: Order) -> "OrderCreatedResponse":
        return OrderCreatedResponse(
            type=ResponseTypes.SUCCESS,
            id=order.id,
            _links=OrderLinks.create(order_id=order.id),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "_links": asdict(self._links),
        }


@dataclass(kw_only=True)
class OrderCancelledResponse(Response):
    id: uuid.UUID

    @staticmethod
    def create(order: Order) -> "OrderCancelledResponse":
        return OrderCancelledResponse(
            type=ResponseTypes.SUCCESS,
            id=order.id,
            _links=OrderLinks.create(order_id=order.id),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "_links": asdict(self._links),
        }
