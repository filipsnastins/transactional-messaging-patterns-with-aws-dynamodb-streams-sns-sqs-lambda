import structlog

from tomodachi_outbox.dynamodb.client import DynamoDBClientFactory
from tomodachi_outbox.dynamodb.session import DynamoDBSession
from tomodachi_outbox.unit_of_work import AbstractUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class BaseDynamoDBUnitOfWork(AbstractUnitOfWork):
    session: DynamoDBSession

    def __init__(self, client_factory: DynamoDBClientFactory, session: DynamoDBSession) -> None:
        self.session = session
        self.client_factory = client_factory

    async def commit(self) -> None:
        items = self.session.get()
        if not items:
            logger.debug("dynamodb_unit_of_work__nothing_to_commit")
            return
        async with self.client_factory() as client:
            try:
                transact_items = [item["transact_item"] for item in items]
                await client.transact_write_items(TransactItems=transact_items)
                logger.debug("dynamodb_unit_of_work__committed", item_count=len(items))
            except client.exceptions.TransactionCanceledException as e:
                cancellation_codes = [reason["Code"] for reason in e.response["CancellationReasons"]]
                raise_on_condition_failures = [item["raise_on_condition_check_failure"] for item in items]
                zipped = zip(cancellation_codes, raise_on_condition_failures)
                for cancellation_code, raise_on_condition_failure in zipped:
                    if cancellation_code == "None":
                        continue
                    if cancellation_code == "ConditionalCheckFailed" and raise_on_condition_failure is not None:
                        raise raise_on_condition_failure from e
                raise
            finally:
                await self.rollback()

    async def rollback(self) -> None:
        self.session.clear()
        logger.debug("dynamodb_unit_of_work__rollback")
