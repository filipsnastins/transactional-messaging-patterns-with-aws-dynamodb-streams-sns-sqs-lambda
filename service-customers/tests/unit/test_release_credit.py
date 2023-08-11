import uuid
from decimal import Decimal

import pytest

from adapters.customer_repository import CustomerNotFoundError
from customers.commands import CreateCustomerCommand, ReleaseCreditCommand, ReserveCreditCommand
from customers.customer import CreditNotReservedForOrderError
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_customer() -> None:
    uow = FakeUnitOfWork()
    release_credit_cmd = ReleaseCreditCommand(customer_id=uuid.uuid4(), order_id=uuid.uuid4())

    with pytest.raises(CustomerNotFoundError, match=str(release_credit_cmd.customer_id)):
        await use_cases.release_credit(uow, release_credit_cmd)


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_order() -> None:
    uow = FakeUnitOfWork()
    create_customer_cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, create_customer_cmd)
    release_credit_cmd = ReleaseCreditCommand(customer_id=customer.id, order_id=uuid.uuid4())

    with pytest.raises(CreditNotReservedForOrderError, match=str(release_credit_cmd.order_id)):
        await use_cases.release_credit(uow, release_credit_cmd)


@pytest.mark.asyncio()
async def test_release_credit() -> None:
    uow = FakeUnitOfWork()
    create_customer_cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, create_customer_cmd)
    reserve_credit_cmd = ReserveCreditCommand(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00")
    )
    await use_cases.reserve_credit(uow, reserve_credit_cmd)

    release_credit_cmd = ReleaseCreditCommand(customer_id=customer.id, order_id=reserve_credit_cmd.order_id)
    await use_cases.release_credit(uow, release_credit_cmd)

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("200.00")
