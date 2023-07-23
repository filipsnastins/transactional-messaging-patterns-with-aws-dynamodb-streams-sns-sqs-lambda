import uuid
from datetime import datetime
from decimal import Decimal

from customers.domain import Customer


def test_create_customer_model() -> None:
    customer_id = uuid.uuid4()
    order_id_1 = uuid.uuid4()
    order_id_2 = uuid.uuid4()
    customer = Customer(
        customer_id=customer_id,
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations={
            order_id_1: Decimal("100.50"),
            order_id_2: Decimal("200.99"),
        },
        created_at=datetime(2021, 1, 1, 12, 0, 0),
        version=0,
    )

    assert customer.customer_id == customer_id
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.credit_reservations == {
        order_id_1: Decimal("100.50"),
        order_id_2: Decimal("200.99"),
    }
    assert customer.created_at == datetime(2021, 1, 1, 12, 0, 0)
    assert customer.version == 0


def test_customer_model_from_dict() -> None:
    customer_id = uuid.uuid4()
    init_dict = {
        "customer_id": customer_id,
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {
            uuid.uuid4(): Decimal("100.50"),
            uuid.uuid4(): Decimal("200.99"),
        },
        "created_at": datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }

    customer = Customer.from_dict(init_dict)

    assert customer.customer_id == customer_id
    assert customer.name == init_dict["name"]
    assert customer.credit_limit == init_dict["credit_limit"]
    assert customer.credit_reservations == init_dict["credit_reservations"]
    assert customer.created_at == init_dict["created_at"]
    assert customer.version == init_dict["version"]


def test_customer_model_to_dict() -> None:
    init_dict = {
        "customer_id": uuid.uuid4(),
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {},
        "created_at": datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }
    customer = Customer.from_dict(init_dict)

    assert customer.to_dict() == init_dict


def test_customer_model_comparison() -> None:
    data = {
        "customer_id": uuid.uuid4(),
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {
            uuid.uuid4(): Decimal("100.50"),
            uuid.uuid4(): Decimal("200.99"),
        },
        "created_at": datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }
    customer_1 = Customer.from_dict(data)
    customer_2 = Customer.from_dict(data)

    assert customer_1 == customer_2
