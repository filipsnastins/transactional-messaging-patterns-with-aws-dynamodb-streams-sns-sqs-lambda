from transactional_outbox import OutboxRepository
from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from unit_of_work import AbstractUnitOfWork
from unit_of_work.dynamodb import BaseDynamoDBUnitOfWork

from adapters import clients, dynamodb, outbox
from adapters.customer_repository import CustomerRepository, DynamoDBCustomerRepository
from service_layer.topics import TOPICS_MAP


class UnitOfWork(AbstractUnitOfWork):
    customers: CustomerRepository
    events: OutboxRepository


class DynamoDBUnitOfWork(UnitOfWork, BaseDynamoDBUnitOfWork):
    customers: DynamoDBCustomerRepository
    events: DynamoDBOutboxRepository

    def __init__(self) -> None:
        super().__init__(clients.get_dynamodb_client)
        self.customers = DynamoDBCustomerRepository(dynamodb.get_customers_table_name(), self.session)
        self.events = DynamoDBOutboxRepository(outbox.get_outbox_table_name(), self.session, TOPICS_MAP)
