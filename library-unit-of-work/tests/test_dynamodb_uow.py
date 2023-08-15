from dataclasses import dataclass
from typing import Protocol

import pytest
import structlog

from unit_of_work.dynamodb.client import DynamoDBClientFactory
from unit_of_work.dynamodb.session import DynamoDBSession
from unit_of_work.uow import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

pytestmark = pytest.mark.usefixtures("_create_dynamodb_table", "_reset_moto_container_on_teardown")


@dataclass
class Product:
    id: str
    name: str


class ProductRepository(Protocol):
    async def create(self, product: Product) -> None:
        ...

    async def get(self, product_id: str) -> Product | None:
        ...


class ProductDynamoDBRepository(ProductRepository):
    def __init__(self, table_name: str, session: DynamoDBSession) -> None:
        self._table_name = table_name
        self._session = session

    async def create(self, product: Product) -> None:
        self._session.add(
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        "PK": {"S": f"PRODUCT#{product.id}"},
                        "Id": {"S": product.id},
                        "Name": {"S": product.name},
                    },
                    "ConditionExpression": "attribute_not_exists(Id)",
                }
            }
        )

    async def get(self, product_id: str) -> Product | None:
        async with self._session.get_client() as client:
            get_item_response = await client.get_item(
                TableName=self._table_name,
                Key={"PK": {"S": f"PRODUCT#{product_id}"}},
            )
            item = get_item_response.get("Item")
            if not item:
                return None
            return Product(
                id=item["Id"]["S"],
                name=item["Name"]["S"],
            )


class UnitOfWork(AbstractUnitOfWork):
    products: ProductRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self


class DynamoDBUnitOfWork(UnitOfWork):
    session: DynamoDBSession
    products: ProductDynamoDBRepository

    def __init__(self, client_factory: DynamoDBClientFactory) -> None:
        self.session = DynamoDBSession(client_factory)
        self.products = ProductDynamoDBRepository(table_name="test-table", session=self.session)

    async def commit(self) -> None:
        await self.session.commit()
        logger.info("dynamodb_unit_of_work__committed")

    async def rollback(self) -> None:
        self.session.rollback()
        logger.info("dynamodb_unit_of_work__rolled_back")


@pytest.mark.asyncio()
async def test_uow_does_not_commit_by_default(client_factory: DynamoDBClientFactory) -> None:
    uow = DynamoDBUnitOfWork(client_factory)
    product = Product(id="product-1111", name="MINIMALIST-SPOON")

    await uow.products.create(product)

    product_from_db = await uow.products.get(product_id="product-1111")
    assert product_from_db is None


@pytest.mark.asyncio()
async def test_commit_uow(client_factory: DynamoDBClientFactory) -> None:
    uow = DynamoDBUnitOfWork(client_factory)
    product = Product(id="product-1111", name="MINIMALIST-SPOON")

    await uow.products.create(product)
    await uow.commit()

    product_from_db = await uow.products.get(product_id="product-1111")
    assert product_from_db
    assert product_from_db.id == "product-1111"
    assert product_from_db.name == "MINIMALIST-SPOON"


@pytest.mark.asyncio()
async def test_multiple_commits(client_factory: DynamoDBClientFactory) -> None:
    uow = DynamoDBUnitOfWork(client_factory)
    product_1 = Product(id="product-1111", name="MINIMALIST-SPOON")
    product_2 = Product(id="product-2222", name="RETRO-CLOCK")

    await uow.products.create(product_1)
    await uow.commit()
    await uow.products.create(product_2)
    await uow.commit()

    product_from_db_1 = await uow.products.get(product_id="product-1111")
    assert product_from_db_1
    assert product_from_db_1.id == "product-1111"
    assert product_from_db_1.name == "MINIMALIST-SPOON"
    product_from_db_2 = await uow.products.get(product_id="product-2222")
    assert product_from_db_2
    assert product_from_db_2.id == "product-2222"
    assert product_from_db_2.name == "RETRO-CLOCK"


@pytest.mark.asyncio()
async def test_uow_context_manager_rollbacks_by_default(client_factory: DynamoDBClientFactory) -> None:
    async with DynamoDBUnitOfWork(client_factory) as uow:
        product = Product(id="product-1111", name="MINIMALIST-SPOON")

        await uow.products.create(product)

    product_from_db = await uow.products.get(product_id="product-1111")
    assert product_from_db is None


@pytest.mark.asyncio()
async def test_commit_uow_in_context_manager(client_factory: DynamoDBClientFactory) -> None:
    async with DynamoDBUnitOfWork(client_factory) as uow:
        product = Product(id="product-1111", name="MINIMALIST-SPOON")

        await uow.products.create(product)
        await uow.commit()

    product_from_db = await uow.products.get(product_id="product-1111")
    assert product_from_db
    assert product_from_db.id == "product-1111"
    assert product_from_db.name == "MINIMALIST-SPOON"
