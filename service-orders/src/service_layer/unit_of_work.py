import structlog
from transactional_outbox import OutboxRepository
from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from unit_of_work import AbstractUnitOfWork
from unit_of_work.dynamodb import BaseDynamoDBUnitOfWork, DynamoDBSession

from adapters import clients, dynamodb, outbox
from adapters.order_repository import DynamoDBOrderRepository, OrderRepository
from service_layer.topics import TOPICS_MAP

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class UnitOfWork(AbstractUnitOfWork):
    orders: OrderRepository
    events: OutboxRepository


class DynamoDBUnitOfWork(UnitOfWork, BaseDynamoDBUnitOfWork):
    orders: DynamoDBOrderRepository
    events: DynamoDBOutboxRepository

    def __init__(self) -> None:
        super().__init__(clients.get_dynamodb_client)

        orders_table_name = dynamodb.get_orders_table_name()
        outbox_table_name = outbox.get_outbox_table_name()

        self.orders = DynamoDBOrderRepository(orders_table_name, self.session)
        self.events = DynamoDBOutboxRepository(outbox_table_name, self.session, TOPICS_MAP)
