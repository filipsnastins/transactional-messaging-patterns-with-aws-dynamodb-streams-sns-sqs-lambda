import datetime
import uuid

from orders.events import Event
from utils.time import utcnow


def test_event_model() -> None:
    event_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    created_at = datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)
    event = Event(
        event_id=event_id,
        correlation_id=correlation_id,
        order_id=order_id,
        customer_id=customer_id,
        created_at=created_at,
    )

    assert event.event_id == event_id
    assert event.correlation_id == correlation_id
    assert event.customer_id == customer_id
    assert event.created_at == created_at


def test_created_at_set_to_current_datetime() -> None:
    event_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    event = Event(
        event_id=event_id,
        correlation_id=correlation_id,
        order_id=order_id,
        customer_id=customer_id,
    )

    assert event.created_at
    assert datetime.timedelta(seconds=1) > utcnow() - event.created_at
    assert event.created_at.tzinfo == datetime.UTC
