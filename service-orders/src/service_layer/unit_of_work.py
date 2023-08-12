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
from adapters.order_repository import DynamoDBOrderRepository, OrderRepository
from service_layer.topics import TOPICS_MAP

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class UnitOfWork(AbstractUnitOfWork):
    orders: OrderRepository
    events: OutboxRepository


class DynamoDBUnitOfWork(UnitOfWork, BaseDynamoDBUnitOfWork):
    session: DynamoDBSession
    orders: DynamoDBOrderRepository
    events: DynamoDBOutboxRepository

    def __init__(
        self,
        client_factory: DynamoDBClientFactory,
        session: DynamoDBSession,
        orders: DynamoDBOrderRepository,
        events: DynamoDBOutboxRepository,
    ) -> None:
        super().__init__(client_factory, session)
        self.orders = orders
        self.events = events

    @staticmethod
    def create() -> "DynamoDBUnitOfWork":
        def client_factory() -> DynamoDBClient:
            return clients.get_dynamodb_client()

        aggregate_table_name = dynamodb.get_aggregate_table_name()
        outbox_table_name = outbox.get_outbox_table_name()

        session = DynamoDBSession()
        customers = DynamoDBOrderRepository(aggregate_table_name, session, client_factory)
        events = DynamoDBOutboxRepository(outbox_table_name, session, client_factory, TOPICS_MAP)
        return DynamoDBUnitOfWork(client_factory, session, customers, events)
