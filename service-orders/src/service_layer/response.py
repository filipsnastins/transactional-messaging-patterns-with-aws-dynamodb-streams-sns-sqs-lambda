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
class OrderLink:
    href: str

    @staticmethod
    def create(order_id: uuid.UUID) -> "OrderLink":
        return OrderLink(href=f"/order/{order_id}")


@dataclass
class SelfOrderLink:
    self: OrderLink

    @staticmethod
    def create(order_id: uuid.UUID) -> "SelfOrderLink":
        return SelfOrderLink(self=OrderLink.create(order_id))


@dataclass
class CreateOrderResponse(Response):
    id: uuid.UUID
    _links: SelfOrderLink

    @staticmethod
    def create(order: Order) -> "CreateOrderResponse":
        _links = SelfOrderLink.create(order_id=order.id)
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
    total_amount: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    _links: SelfOrderLink

    @staticmethod
    def create(order: Order) -> "GetOrderResponse":
        return GetOrderResponse(
            id=order.id,
            customer_id=order.customer_id,
            state=order.state,
            total_amount=order.total_amount,
            version=order.version,
            created_at=order.created_at,
            updated_at=order.updated_at,
            _links=SelfOrderLink.create(order_id=order.id),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "state": self.state.value,
            "total_amount": int(Money(self.total_amount).to_sub_units()),
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
    id: uuid.UUID
    _links: SelfOrderLink
    error: ErrorCodes = ErrorCodes.ORDER_NOT_FOUND

    @staticmethod
    def create(order_id: uuid.UUID) -> "OrderNotFoundResponse":
        return OrderNotFoundResponse(id=order_id, _links=SelfOrderLink.create(order_id))

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "error": self.error.value,
            "_links": asdict(self._links),
        }

    @property
    def status_code(self) -> int:
        return 404
