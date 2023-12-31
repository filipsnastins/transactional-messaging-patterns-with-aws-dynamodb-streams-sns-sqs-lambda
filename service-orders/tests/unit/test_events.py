import datetime
import json
import uuid

from orders.events import Event
from orders.order import OrderState
from utils.time import utcnow


def test_event_model() -> None:
    event_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    event = Event(
        event_id=event_id,
        correlation_id=correlation_id,
        order_id=order_id,
        customer_id=customer_id,
        state=OrderState.PENDING,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert event.event_id == event_id
    assert event.message_id == event_id
    assert event.correlation_id == correlation_id
    assert event.order_id == order_id
    assert event.aggregate_id == order_id
    assert event.customer_id == customer_id
    assert event.state == OrderState.PENDING
    assert event.created_at == datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC)


def test_created_at_set_to_current_datetime() -> None:
    event_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    event = Event(
        event_id=event_id,
        correlation_id=correlation_id,
        order_id=order_id,
        state=OrderState.PENDING,
        customer_id=customer_id,
    )

    assert event.created_at
    assert datetime.timedelta(seconds=1) > utcnow() - event.created_at
    assert event.created_at.tzinfo == datetime.UTC


def test_event_to_dict() -> None:
    event_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    event = Event(
        event_id=event_id,
        correlation_id=correlation_id,
        order_id=order_id,
        customer_id=customer_id,
        state=OrderState.PENDING,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert event.to_dict() == {
        "event_id": str(event_id),
        "correlation_id": str(correlation_id),
        "order_id": str(order_id),
        "customer_id": str(customer_id),
        "state": OrderState.PENDING.value,
        "created_at": "2021-01-01T12:00:00+00:00",
    }


def test_serialize_event_model_to_json() -> None:
    event_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    event = Event(
        event_id=event_id,
        correlation_id=correlation_id,
        order_id=order_id,
        customer_id=customer_id,
        state=OrderState.PENDING,
        created_at=datetime.datetime(2021, 1, 1, 12, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert json.loads(event.serialize()) == event.to_dict()
