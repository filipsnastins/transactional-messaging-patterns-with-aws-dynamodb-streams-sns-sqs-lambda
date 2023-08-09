import datetime
import uuid
from decimal import Decimal

from orders.order import Order, OrderState
from utils.time import utcnow


def test_create_new_order_model() -> None:
    customer_id = uuid.uuid4()

    order = Order.create(customer_id=customer_id, total_amount=Decimal("200.00"))

    assert isinstance(order.id, uuid.UUID)
    assert order.customer_id == customer_id
    assert order.state == OrderState.PENDING
    assert order.total_amount == Decimal("200.00")
    assert datetime.timedelta(seconds=1) > utcnow() - order.created_at
    assert order.version == 0
    assert order.created_at.tzinfo == datetime.UTC
    assert order.updated_at is None


def test_init_customer_model() -> None:
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    order = Order(
        id=order_id,
        customer_id=customer_id,
        state=OrderState.PENDING,
        total_amount=Decimal("200.00"),
        version=0,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert order.id == order_id
    assert order.customer_id == customer_id
    assert order.state == OrderState.PENDING
    assert order.total_amount == Decimal("200.00")
    assert order.version == 0
    assert order.created_at == datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)
    assert order.updated_at == datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)


def test_order_model_comparison() -> None:
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    order_1 = Order(
        id=order_id,
        customer_id=customer_id,
        state=OrderState.PENDING,
        total_amount=Decimal("200.00"),
        version=0,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    order_2 = Order(
        id=order_id,
        customer_id=customer_id,
        state=OrderState.PENDING,
        total_amount=Decimal("200.00"),
        version=0,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert order_1 == order_2
    assert order_1 is not order_2
