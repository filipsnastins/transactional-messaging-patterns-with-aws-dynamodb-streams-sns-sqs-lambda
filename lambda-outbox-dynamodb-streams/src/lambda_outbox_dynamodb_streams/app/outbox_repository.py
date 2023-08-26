from transactional_messaging.dynamodb import DynamoDBOutboxRepository
from unit_of_work.dynamodb import DynamoDBSession

from . import clients
from .settings import get_settings


def create_outbox_repository() -> DynamoDBOutboxRepository:
    settings = get_settings()
    session = DynamoDBSession(clients.get_dynamodb_client)
    return DynamoDBOutboxRepository(table_name=settings.dynamodb_outbox_table_name, session=session, topic_map={})
