import uuid
from datetime import datetime
from decimal import Decimal

from customers.events import CustomerCreatedEvent


def test_create_customer_created_event_model() -> None:
    event_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    event = CustomerCreatedEvent(
        event_id=event_id,
        customer_id=customer_id,
        name="John Doe",
        credit_limit=Decimal("1000.00"),
        created_at=datetime(2021, 1, 1, 12, 0, 0),
    )

    assert event.event_id == event_id
    assert event.customer_id == customer_id
    assert event.name == "John Doe"
    assert event.credit_limit == Decimal("1000.00")
    assert event.created_at == datetime(2021, 1, 1, 12, 0, 0)
