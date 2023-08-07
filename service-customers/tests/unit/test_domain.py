import datetime
import uuid
from decimal import Decimal

import pytest
from freezegun import freeze_time

from customers.customer import Customer, CustomerCreditLimitExceededError
from customers.events import CustomerCreatedEvent


@freeze_time("2021-02-03 12:30:00")
def test_create_new_customer_model() -> None:
    correlation_id = uuid.uuid4()
    [customer, event] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=correlation_id)

    assert isinstance(customer.id, uuid.UUID)
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.created_at == datetime.datetime(2021, 2, 3, 12, 30, 0, tzinfo=datetime.timezone.utc)
    assert customer.version == 0
    assert isinstance(event.event_id, uuid.UUID)
    assert event == CustomerCreatedEvent(
        event_id=event.event_id,
        correlation_id=correlation_id,
        customer_id=customer.id,
        name=customer.name,
        credit_limit=customer.credit_limit,
        created_at=customer.created_at,
    )


def test_restore_customer_model() -> None:
    id = uuid.uuid4()
    customer = Customer(
        id=id,
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations={
            uuid.uuid4(): Decimal("50.00"),
            uuid.uuid4(): Decimal("49.99"),
        },
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0),
        version=0,
    )

    assert customer.id == id
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.created_at == datetime.datetime(2021, 1, 1, 12, 0, 0)
    assert customer.version == 0


def test_customer_model_from_dict() -> None:
    id = uuid.uuid4()
    init_dict = {
        "id": id,
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {
            uuid.uuid4(): Decimal("50.00"),
            uuid.uuid4(): Decimal("49.99"),
        },
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }

    customer = Customer.from_dict(init_dict)

    assert customer.id == id
    assert customer.name == init_dict["name"]
    assert customer.credit_limit == Decimal("200.00")
    assert customer.created_at == init_dict["created_at"]
    assert customer.version == init_dict["version"]
    assert customer.available_credit() == Decimal("100.01")


def test_customer_model_to_dict() -> None:
    customer_id = uuid.uuid4()
    init_dict = {
        "id": customer_id,
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {},
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }
    customer = Customer.from_dict(init_dict)

    assert customer.to_dict() == {
        "id": str(customer_id),
        "name": init_dict["name"],
        "credit_limit": 20000,
        "credit_reservations": {},
        "created_at": "2021-01-01T12:00:00",
        "version": 0,
    }


def test_customer_model_comparison() -> None:
    data = {
        "id": uuid.uuid4(),
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {
            uuid.uuid4(): Decimal("50.00"),
            uuid.uuid4(): Decimal("49.99"),
        },
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }
    customer_1 = Customer.from_dict(data)
    customer_2 = Customer.from_dict(data)

    assert customer_1 == customer_2


def test_unreserve_credit() -> None:
    [customer, _] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())
    id = uuid.uuid4()
    customer.reserve_credit(order_id=id, order_total=Decimal("100.00"))

    customer.unreserve_credit(id=id)

    assert customer.available_credit() == Decimal("200.00")


def test_unreserve_non_existing_order_raises_key_error() -> None:
    [customer, _] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())

    with pytest.raises(KeyError):
        customer.unreserve_credit(id=uuid.uuid4())
