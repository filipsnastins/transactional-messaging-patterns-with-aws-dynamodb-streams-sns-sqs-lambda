import pytest
import pytest_asyncio
from botocore.exceptions import ClientError
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

from unit_of_work.dynamodb import DynamoDBSession
from unit_of_work.dynamodb.client import DynamoDBClientFactory

pytestmark = pytest.mark.usefixtures("_create_dynamodb_table", "_reset_moto_container_on_teardown")


@pytest_asyncio.fixture()
async def session(client_factory: DynamoDBClientFactory) -> DynamoDBSession:
    return DynamoDBSession(client_factory)


@pytest.mark.asyncio()
async def test_commit_session(session: DynamoDBSession) -> None:
    transact_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        }
    }
    transact_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        }
    }
    session.add(transact_item_1)
    session.add(transact_item_2)

    await session.commit()

    async with session.get_client() as client:
        scan_table_response = await client.scan(TableName="test-table")
        assert scan_table_response["Items"] == [{"PK": {"S": "item-1111"}}, {"PK": {"S": "item-2222"}}]
        assert scan_table_response["Count"] == 2


@pytest.mark.asyncio()
async def test_rollback_session(session: DynamoDBSession) -> None:
    transact_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        }
    }
    transact_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        }
    }
    session.add(transact_item_1)
    session.add(transact_item_2)

    session.rollback()
    await session.commit()

    async with session.get_client() as client:
        scan_table_response = await client.scan(TableName="test-table")
        assert scan_table_response["Count"] == 0


@pytest.mark.asyncio()
async def test_session_cleared_after_commit(session: DynamoDBSession) -> None:
    transact_item: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        },
    }
    session.add(transact_item)

    await session.commit()
    await session.commit()  # Should not attempt to commit the item again, otherwise will fail on ConditionExpression


@pytest.mark.asyncio()
async def test_raise_dynamodb_exception(session: DynamoDBSession) -> None:
    transact_item: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        },
    }
    session.add(transact_item)
    await session.commit()

    session.add(transact_item)

    with pytest.raises(ClientError) as exc_info:
        await session.commit()
    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"
    async with session.get_client() as client:
        get_item_response = await client.get_item(TableName="test-table", Key={"PK": {"S": "item-1111"}})
        assert "Item" in get_item_response


@pytest.mark.asyncio()
async def test_raise_domain_exception(session: DynamoDBSession) -> None:
    transact_item: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(PK)",
        },
    }
    session.add(transact_item)
    await session.commit()

    session.add(transact_item, raise_on_condition_check_failure=RuntimeError("Item already exists"))

    with pytest.raises(RuntimeError, match="Item already exists"):
        await session.commit()
    async with session.get_client() as client:
        get_item_response = await client.get_item(TableName="test-table", Key={"PK": {"S": "item-1111"}})
        assert "Item" in get_item_response


@pytest.mark.asyncio()
async def test_dynamodb_exception_raised_for_first_failing_item(session: DynamoDBSession) -> None:
    session.add({"Put": {"TableName": "test-table", "Item": {"PK": {"S": "item-2222"}}}})
    await session.commit()

    passing_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
        }
    }
    failing_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(PK)",  # This will fail
        }
    }
    passing_item_3: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-3333"}},
        }
    }
    session.add(passing_item_1)
    session.add(failing_item_2)
    session.add(passing_item_3)

    with pytest.raises(ClientError) as exc_info:
        await session.commit()
    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"
    cancellation_codes = [reason["Code"] for reason in exc_info.value.response["CancellationReasons"]]
    assert cancellation_codes == ["None", "ConditionalCheckFailed", "None"]


@pytest.mark.asyncio()
async def test_domain_error_raised_for_first_failing_item(session: DynamoDBSession) -> None:
    session.add({"Put": {"TableName": "test-table", "Item": {"PK": {"S": "item-2222"}}}})
    await session.commit()

    passing_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-1111"}},
        }
    }
    failing_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(PK)",  # This will fail
        }
    }
    passing_item_3: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "test-table",
            "Item": {"PK": {"S": "item-3333"}},
        }
    }
    session.add(passing_item_1)
    session.add(failing_item_2, raise_on_condition_check_failure=RuntimeError("Item already exists"))
    session.add(passing_item_3)

    with pytest.raises(RuntimeError, match="Item already exists"):
        await session.commit()
