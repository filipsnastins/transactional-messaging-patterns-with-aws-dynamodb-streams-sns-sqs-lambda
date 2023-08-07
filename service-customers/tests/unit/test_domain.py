import datetime
import uuid
from decimal import Decimal

from freezegun import freeze_time

from customers.customer import Customer


@freeze_time("2021-02-03 12:30:00")
def test_create_new_customer_model() -> None:
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    assert isinstance(customer.id, uuid.UUID)
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.version == 0
    assert customer.created_at == datetime.datetime(2021, 2, 3, 12, 30, 0, tzinfo=datetime.UTC)
    assert customer.updated_at is None


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
        version=0,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert customer.id == id
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.version == 0
    assert customer.created_at == datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)
    assert customer.updated_at == datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)


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
        "version": 0,
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        "updated_at": None,
    }

    customer = Customer.from_dict(init_dict)

    assert customer.id == id
    assert customer.name == init_dict["name"]
    assert customer.credit_limit == Decimal("200.00")
    assert customer.version == init_dict["version"]
    assert customer.created_at == init_dict["created_at"]
    assert customer.updated_at is None
    assert customer.available_credit() == Decimal("100.01")


def test_customer_model_to_dict() -> None:
    id = uuid.uuid4()
    init_dict = {
        "id": id,
        "name": "John Doe",
        "credit_limit": Decimal("200.00"),
        "credit_reservations": {},
        "version": 0,
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        "updated_at": datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    }
    customer = Customer.from_dict(init_dict)

    assert customer.to_dict() == {
        "id": str(id),
        "name": init_dict["name"],
        "credit_limit": 20000,
        "credit_reservations": {},
        "version": 0,
        "created_at": "2021-01-01T12:00:00+00:00",
        "updated_at": "2022-01-01T12:00:00+00:00",
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
        "version": 0,
        "created_at": datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
        "updated_at": datetime.datetime(2022, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    }
    customer_1 = Customer.from_dict(data)
    customer_2 = Customer.from_dict(data)

    assert customer_1 == customer_2
