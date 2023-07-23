import uuid

from orders.domain import Order


def test_create_order_model() -> None:
    order_id = uuid.uuid4()
    order = Order(order_id=order_id)

    assert order.order_id == order_id
