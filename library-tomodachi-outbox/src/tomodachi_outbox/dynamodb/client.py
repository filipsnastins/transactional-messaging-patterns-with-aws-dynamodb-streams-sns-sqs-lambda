from typing import Callable

from types_aiobotocore_dynamodb import DynamoDBClient

DynamoDBClientFactory = Callable[[], DynamoDBClient]
