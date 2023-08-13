import pytest
import pytest_asyncio
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from tomodachi_testcontainers.containers import MotoContainer
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef

from tomodachi_outbox.dynamodb import DynamoDBSession

pytestmark = pytest.mark.usefixtures("_create_table", "_reset_moto_container_on_teardown")


@pytest_asyncio.fixture()
async def _create_table(moto_dynamodb_client: DynamoDBClient) -> None:
    await moto_dynamodb_client.create_table(
        TableName="TestTable",
        AttributeDefinitions=[{"AttributeName": "Id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "Id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest_asyncio.fixture()
async def session(moto_container: MotoContainer) -> DynamoDBSession:
    def client_factory() -> DynamoDBClient:
        return get_session().create_client("dynamodb", **moto_container.get_aws_client_config())

    return DynamoDBSession(client_factory)


@pytest.mark.asyncio()
async def test_commit_session(session: DynamoDBSession, moto_dynamodb_client: DynamoDBClient) -> None:
    transact_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        }
    }
    transact_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        }
    }
    session.add(transact_item_1)
    session.add(transact_item_2)

    await session.commit()

    scan_table_response = await moto_dynamodb_client.scan(TableName="TestTable")
    assert scan_table_response["Items"] == [{"Id": {"S": "item-1111"}}, {"Id": {"S": "item-2222"}}]
    assert scan_table_response["Count"] == 2


@pytest.mark.asyncio()
async def test_rollback_session(session: DynamoDBSession, moto_dynamodb_client: DynamoDBClient) -> None:
    transact_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        }
    }
    transact_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        }
    }
    session.add(transact_item_1)
    session.add(transact_item_2)

    session.rollback()
    await session.commit()

    scan_table_response = await moto_dynamodb_client.scan(TableName="TestTable")
    assert scan_table_response["Count"] == 0


@pytest.mark.asyncio()
async def test_session_cleared_after_commit(session: DynamoDBSession) -> None:
    transact_item: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        },
    }
    session.add(transact_item)

    await session.commit()
    await session.commit()  # Should not attempt to commit the item again, otherwise will fail on ConditionExpression


@pytest.mark.asyncio()
async def test_raise_dynamodb_exception(session: DynamoDBSession, moto_dynamodb_client: DynamoDBClient) -> None:
    transact_item: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        },
    }
    session.add(transact_item)
    await session.commit()

    session.add(transact_item)

    with pytest.raises(ClientError) as exc_info:
        await session.commit()
    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"
    get_item_response = await moto_dynamodb_client.get_item(TableName="TestTable", Key={"Id": {"S": "item-1111"}})
    assert "Item" in get_item_response


@pytest.mark.asyncio()
async def test_raise_domain_exception(session: DynamoDBSession, moto_dynamodb_client: DynamoDBClient) -> None:
    transact_item: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
            "ConditionExpression": "attribute_not_exists(Id)",
        },
    }
    session.add(transact_item)
    await session.commit()

    session.add(transact_item, raise_on_condition_check_failure=RuntimeError("Item already exists"))

    with pytest.raises(RuntimeError, match="Item already exists"):
        await session.commit()
    get_item_response = await moto_dynamodb_client.get_item(TableName="TestTable", Key={"Id": {"S": "item-1111"}})
    assert "Item" in get_item_response


@pytest.mark.asyncio()
async def test_dynamodb_exception_raised_for_first_failing_item(session: DynamoDBSession) -> None:
    session.add({"Put": {"TableName": "TestTable", "Item": {"Id": {"S": "item-2222"}}}})
    await session.commit()

    passing_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
        }
    }
    failing_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(Id)",  # This will fail
        }
    }
    passing_item_3: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-3333"}},
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
    session.add({"Put": {"TableName": "TestTable", "Item": {"Id": {"S": "item-2222"}}}})
    await session.commit()

    passing_item_1: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-1111"}},
        }
    }
    failing_item_2: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-2222"}},
            "ConditionExpression": "attribute_not_exists(Id)",  # This will fail
        }
    }
    passing_item_3: TransactWriteItemTypeDef = {
        "Put": {
            "TableName": "TestTable",
            "Item": {"Id": {"S": "item-3333"}},
        }
    }
    session.add(passing_item_1)
    session.add(failing_item_2, raise_on_condition_check_failure=RuntimeError("Item already exists"))
    session.add(passing_item_3)

    with pytest.raises(RuntimeError, match="Item already exists"):
        await session.commit()
