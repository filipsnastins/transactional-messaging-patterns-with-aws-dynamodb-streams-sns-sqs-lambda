import datetime
import uuid
from decimal import Decimal

from customers.customer import Customer
from utils.time import utcnow


def test_create_new_customer_model() -> None:
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    assert isinstance(customer.id, uuid.UUID)
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.credit_reservations == {}
    assert customer.version == 0
    assert datetime.timedelta(seconds=1) > utcnow() - customer.created_at
    assert customer.created_at.tzinfo == datetime.UTC
    assert customer.updated_at is None


def test_init_customer_model() -> None:
    customer_id = uuid.uuid4()
    credit_reservations = {uuid.uuid4(): Decimal("50.00"), uuid.uuid4(): Decimal("49.99")}
    customer = Customer(
        id=customer_id,
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations=credit_reservations,
        version=0,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert customer.id == customer_id
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.credit_reservations == credit_reservations
    assert customer.version == 0
    assert customer.created_at == datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)
    assert customer.updated_at == datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)


def test_customer_model_comparison() -> None:
    customer_id = uuid.uuid4()
    name = "John Doe"
    credit_limit = Decimal("200.00")
    credit_reservations = {uuid.uuid4(): Decimal("50.00"), uuid.uuid4(): Decimal("49.99")}
    version = 0
    created_at = datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)
    updated_at = datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)

    customer_1 = Customer(
        id=customer_id,
        name=name,
        credit_limit=credit_limit,
        credit_reservations=credit_reservations,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )
    customer_2 = Customer(
        id=customer_id,
        name=name,
        credit_limit=credit_limit,
        credit_reservations=credit_reservations,
        version=version,
        created_at=created_at,
        updated_at=updated_at,
    )

    assert customer_1 == customer_2
