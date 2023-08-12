from orders.events import Event, OrderApprovedEvent, OrderCancelledEvent, OrderCreatedEvent, OrderRejectedEvent

TOPICS_MAP: dict[type[Event], str] = {
    OrderApprovedEvent: "order--approved",
    OrderCancelledEvent: "order--cancelled",
    OrderCreatedEvent: "order--created",
    OrderRejectedEvent: "order--rejected",
}
