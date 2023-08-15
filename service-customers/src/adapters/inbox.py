from transactional_outbox.dynamodb import create_inbox_table as transactional_outbox_create_inbox_table

from adapters import clients
from adapters.settings import get_settings


def get_inbox_table_name() -> str:
    return get_settings().dynamodb_inbox_table_name


async def create_inbox_table() -> None:
    async with clients.get_dynamodb_client() as client:
        await transactional_outbox_create_inbox_table(table_name=get_inbox_table_name(), client=client)
