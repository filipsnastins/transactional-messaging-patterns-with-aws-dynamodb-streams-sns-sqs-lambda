import uuid

from orders.domain import Order


def test_create_order_model() -> None:
    id = uuid.uuid4()
    order = Order(id=id)

    assert order.id == id
