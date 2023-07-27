import datetime
import uuid
from decimal import Decimal

import pytest
from customers.customer import Customer, CustomerCreditLimitExceededError
from customers.events import CustomerCreatedEvent
from freezegun import freeze_time


@freeze_time("2021-02-03 12:30:00")
def test_create_new_customer_model() -> None:
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    assert isinstance(customer.id, uuid.UUID)
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.created_at == datetime.datetime(2021, 2, 3, 12, 30, 0, tzinfo=datetime.UTC)
    assert customer.version == 0
    assert isinstance(customer.events[0].event_id, uuid.UUID)
    assert customer.events == [
        CustomerCreatedEvent(
            event_id=customer.events[0].event_id,
            customer_id=customer.id,
            name=customer.name,
            credit_limit=customer.credit_limit,
            created_at=customer.created_at,
        )
    ]


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
    assert customer.events == []


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
    assert customer.events == []


def test_customer_model_to_dict() -> None:
    init_dict = {
        "id": uuid.uuid4(),
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {},
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "version": 0,
    }
    customer = Customer.from_dict(init_dict)

    assert customer.to_dict() == init_dict


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


@pytest.mark.parametrize(
    ("credit_limit", "order_total", "expected"),
    [
        (Decimal("200.00"), Decimal("0"), Decimal("200.00")),
        (Decimal("200.00"), Decimal("100.00"), Decimal("100.00")),
        (Decimal("200.00"), Decimal("100.01"), Decimal("99.99")),
        (Decimal("200.00"), Decimal("200.00"), Decimal("0.00")),
    ],
)
def test_reserve_credit(credit_limit: Decimal, order_total: Decimal, expected: Decimal) -> None:
    customer = Customer.create(name="John Doe", credit_limit=credit_limit)

    customer.reserve_credit(id=uuid.uuid4(), order_total=order_total)

    assert customer.available_credit() == expected


def test_insufficient_credit_raises_credit_limit_exceeded_error() -> None:
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    with pytest.raises(CustomerCreditLimitExceededError):
        customer.reserve_credit(id=uuid.uuid4(), order_total=Decimal("200.01"))

    assert customer.available_credit() == Decimal("200.00")


def test_unreserve_credit() -> None:
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
    id = uuid.uuid4()
    customer.reserve_credit(id=id, order_total=Decimal("100.00"))

    customer.unreserve_credit(id=id)

    assert customer.available_credit() == Decimal("200.00")


def test_unreserve_non_existing_order_raises_key_error() -> None:
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    with pytest.raises(KeyError):
        customer.unreserve_credit(id=uuid.uuid4())
