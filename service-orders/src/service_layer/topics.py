from orders.events import Event, OrderCreatedEvent

TOPICS_MAP: dict[type[Event], str] = {
    OrderCreatedEvent: "order--created",
}
