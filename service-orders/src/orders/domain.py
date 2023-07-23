import uuid
from dataclasses import dataclass


@dataclass
class Order:
    order_id: uuid.UUID
