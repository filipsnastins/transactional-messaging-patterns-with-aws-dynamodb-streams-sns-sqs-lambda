import uuid

import structlog
from transactional_outbox import InboxRepository, OutboxRepository, ensure_idempotence
from transactional_outbox.dynamodb import DynamoDBInboxRepository, DynamoDBOutboxRepository
from unit_of_work import AbstractUnitOfWork
from unit_of_work.dynamodb import DynamoDBSession

from adapters import clients, dynamodb, inbox, outbox
from adapters.customer_repository import CustomerRepository, DynamoDBCustomerRepository
from service_layer.topics import TOPICS_MAP

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class UnitOfWork(AbstractUnitOfWork):
    customers: CustomerRepository
    inbox: InboxRepository
    events: OutboxRepository

    def __init__(self, message_id: uuid.UUID | None = None) -> None:
        self.message_id = message_id

    async def __aenter__(self) -> "UnitOfWork":
        if self.message_id:
            await ensure_idempotence(message_id=self.message_id, repository=self.inbox)
        return self


class DynamoDBUnitOfWork(UnitOfWork):
    customers: DynamoDBCustomerRepository
    inbox: DynamoDBInboxRepository
    events: DynamoDBOutboxRepository

    def __init__(self, message_id: uuid.UUID | None = None) -> None:
        super().__init__(message_id=message_id)
        self.session = DynamoDBSession(clients.get_dynamodb_client)
        self.customers = DynamoDBCustomerRepository(dynamodb.get_customers_table_name(), self.session)
        self.inbox = DynamoDBInboxRepository(inbox.get_inbox_table_name(), self.session)
        self.events = DynamoDBOutboxRepository(outbox.get_outbox_table_name(), self.session, TOPICS_MAP)

    async def commit(self) -> None:
        await self.session.commit()
        logger.info("dynamodb_unit_of_work__committed")

    async def rollback(self) -> None:
        self.session.rollback()
        logger.info("dynamodb_unit_of_work__rolled_back")
