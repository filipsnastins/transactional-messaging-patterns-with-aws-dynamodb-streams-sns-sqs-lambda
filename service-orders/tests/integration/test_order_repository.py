import uuid
from decimal import Decimal

import pytest

from adapters.order_repository import OptimisticLockError, OrderAlreadyExistsError, OrderNotFoundError
from orders.order import Order, OrderState
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_create_order() -> None:
    uow = DynamoDBUnitOfWork.create()
    order = Order.create(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))

    await uow.orders.create(order)
    await uow.commit()

    order_from_db = await uow.orders.get(order.id)
    assert order_from_db == order


@pytest.mark.asyncio()
async def test_order_already_exists() -> None:
    uow = DynamoDBUnitOfWork.create()
    order = Order.create(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))
    await uow.orders.create(order)
    await uow.commit()

    await uow.orders.create(order)
    with pytest.raises(OrderAlreadyExistsError, match=str(order.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_update_non_existing_order() -> None:
    uow = DynamoDBUnitOfWork.create()
    order = Order.create(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))

    await uow.orders.update(order)

    with pytest.raises(OrderNotFoundError, match=str(order.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_update_order() -> None:
    uow = DynamoDBUnitOfWork.create()
    order = Order.create(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))
    await uow.orders.create(order)
    await uow.commit()

    order.state = OrderState.APPROVED
    order.total_amount = Decimal("99.77")
    await uow.orders.update(order)
    await uow.commit()
    order_from_db = await uow.orders.get(order.id)

    assert order_from_db
    assert order_from_db.state == OrderState.APPROVED
    assert order_from_db.total_amount == Decimal("99.77")
    assert order_from_db.version == 1
    assert order_from_db.created_at == order.created_at
    assert order_from_db.updated_at
    assert order_from_db.updated_at > order.created_at


@pytest.mark.asyncio()
async def test_concurrent_order_update_raises_optimistic_lock_error() -> None:
    uow = DynamoDBUnitOfWork.create()
    order = Order.create(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))
    await uow.orders.create(order)
    await uow.commit()

    order.state = OrderState.APPROVED
    await uow.orders.update(order)
    await uow.commit()

    order.state = OrderState.REJECTED
    await uow.orders.update(order)
    with pytest.raises(OptimisticLockError):
        await uow.commit()

    customer_from_db = await uow.orders.get(order.id)
    assert customer_from_db
    assert customer_from_db.state == OrderState.APPROVED
    assert customer_from_db.version == 1
