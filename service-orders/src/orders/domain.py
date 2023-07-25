import uuid
from dataclasses import dataclass


@dataclass
class Order:
    id: uuid.UUID
