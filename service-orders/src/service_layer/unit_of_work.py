from transactional_outbox import OutboxRepository
from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from unit_of_work import AbstractUnitOfWork
from unit_of_work.dynamodb import BaseDynamoDBUnitOfWork

from adapters import clients, dynamodb, outbox
from adapters.order_repository import DynamoDBOrderRepository, OrderRepository
from service_layer.topics import TOPICS_MAP


class UnitOfWork(AbstractUnitOfWork):
    orders: OrderRepository
    events: OutboxRepository


class DynamoDBUnitOfWork(UnitOfWork, BaseDynamoDBUnitOfWork):
    orders: DynamoDBOrderRepository
    events: DynamoDBOutboxRepository

    def __init__(self) -> None:
        super().__init__(clients.get_dynamodb_client)
        self.orders = DynamoDBOrderRepository(dynamodb.get_orders_table_name(), self.session)
        self.events = DynamoDBOutboxRepository(outbox.get_outbox_table_name(), self.session, TOPICS_MAP)
