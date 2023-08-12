import uuid
from decimal import Decimal

import pytest

from adapters.customer_repository import CustomerNotFoundError
from customers.commands import ReleaseCreditCommand, ReserveCreditCommand
from customers.customer import CreditNotReservedForOrderError, Customer
from service_layer import use_cases
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_customer(uow: FakeUnitOfWork) -> None:
    release_credit_cmd = ReleaseCreditCommand(customer_id=uuid.uuid4(), order_id=uuid.uuid4())

    with pytest.raises(CustomerNotFoundError, match=str(release_credit_cmd.customer_id)):
        await use_cases.release_credit(uow, release_credit_cmd)


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_order(uow: FakeUnitOfWork, customer: Customer) -> None:
    cmd = ReleaseCreditCommand(customer_id=customer.id, order_id=uuid.uuid4())

    with pytest.raises(CreditNotReservedForOrderError, match=str(cmd.order_id)):
        await use_cases.release_credit(uow, cmd)


@pytest.mark.asyncio()
async def test_release_credit(uow: FakeUnitOfWork, customer: Customer) -> None:
    customer.credit_limit = Decimal("300.99")
    await uow.customers.update(customer)
    cmd = ReserveCreditCommand(customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00"))
    await use_cases.reserve_credit(uow, cmd)

    await use_cases.release_credit(uow, ReleaseCreditCommand(customer_id=customer.id, order_id=cmd.order_id))

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("300.99")
