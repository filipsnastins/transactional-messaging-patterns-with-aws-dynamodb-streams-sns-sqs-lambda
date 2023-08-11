from orders.events import Event, OrderApprovedEvent, OrderCreatedEvent

TOPICS_MAP: dict[type[Event], str] = {
    OrderCreatedEvent: "order--created",
    OrderApprovedEvent: "order--approved",
}
