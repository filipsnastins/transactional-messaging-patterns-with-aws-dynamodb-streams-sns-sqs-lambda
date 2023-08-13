import structlog
from tomodachi_outbox import AbstractUnitOfWork, OutboxRepository
from tomodachi_outbox.dynamodb import (
    BaseDynamoDBUnitOfWork,
    DynamoDBClientFactory,
    DynamoDBOutboxRepository,
    DynamoDBSession,
)
from types_aiobotocore_dynamodb import DynamoDBClient

from adapters import clients, dynamodb, outbox
from adapters.customer_repository import CustomerRepository, DynamoDBCustomerRepository
from service_layer.topics import TOPICS_MAP

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class UnitOfWork(AbstractUnitOfWork):
    customers: CustomerRepository
    events: OutboxRepository


class DynamoDBUnitOfWork(UnitOfWork, BaseDynamoDBUnitOfWork):
    session: DynamoDBSession
    customers: DynamoDBCustomerRepository
    events: DynamoDBOutboxRepository

    def __init__(
        self,
        client_factory: DynamoDBClientFactory,
        session: DynamoDBSession,
        customers: DynamoDBCustomerRepository,
        events: DynamoDBOutboxRepository,
    ) -> None:
        super().__init__(client_factory, session)
        self.customers = customers
        self.events = events

    @staticmethod
    def create() -> "DynamoDBUnitOfWork":
        client_factory = clients.get_dynamodb_client
        session = DynamoDBSession()

        aggregate_table_name = dynamodb.get_aggregate_table_name()
        outbox_table_name = outbox.get_outbox_table_name()

        orders = DynamoDBCustomerRepository(aggregate_table_name, session, client_factory)
        events = DynamoDBOutboxRepository(outbox_table_name, session, client_factory, TOPICS_MAP)

        return DynamoDBUnitOfWork(client_factory, session, orders, events)
