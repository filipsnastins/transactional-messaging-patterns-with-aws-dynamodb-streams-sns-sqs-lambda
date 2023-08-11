import datetime
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol

from stockholm import Money

from orders.order import Order, OrderState
from utils.time import datetime_to_str


class Response(Protocol):
    @property
    def status_code(self) -> int:
        ...


class ErrorCodes(Enum):
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"


class ErrorResponse(Response, Protocol):
    error: ErrorCodes


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


@dataclass
class CreateOrderResponse(Response):
    id: uuid.UUID
    _links: OrderLinks

    @staticmethod
    def create(order: Order) -> "CreateOrderResponse":
        _links = OrderLinks.create(order_id=order.id)
        return CreateOrderResponse(id=order.id, _links=_links)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "_links": asdict(self._links),
        }

    @property
    def status_code(self) -> int:
        return 200


@dataclass
class GetOrderResponse(Response):
    id: uuid.UUID
    customer_id: uuid.UUID
    state: OrderState
    order_total: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    _links: OrderLinks

    @staticmethod
    def create(order: Order) -> "GetOrderResponse":
        return GetOrderResponse(
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

    @property
    def status_code(self) -> int:
        return 200


@dataclass
class OrderNotFoundResponse(ErrorResponse):
    _links: OrderLinks
    error: ErrorCodes = ErrorCodes.ORDER_NOT_FOUND

    @staticmethod
    def create(order_id: uuid.UUID) -> "OrderNotFoundResponse":
        return OrderNotFoundResponse(_links=OrderLinks.create(order_id))

    def to_dict(self) -> dict:
        return {
            "error": self.error.value,
            "_links": asdict(self._links),
        }

    @property
    def status_code(self) -> int:
        return 404
