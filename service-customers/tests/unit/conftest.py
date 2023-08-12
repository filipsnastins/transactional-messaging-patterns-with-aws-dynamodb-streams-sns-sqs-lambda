import pytest

from tests.unit.fakes import FakeUnitOfWork


@pytest.fixture()
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()
