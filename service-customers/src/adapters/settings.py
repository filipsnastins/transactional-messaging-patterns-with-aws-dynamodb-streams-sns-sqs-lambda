from functools import lru_cache

from tomodachi_bootstrap import TomodachiBaseSettings


class Settings(TomodachiBaseSettings):
    dynamodb_customers_table_name: str
    dynamodb_inbox_table_name: str
    dynamodb_outbox_table_name: str


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
