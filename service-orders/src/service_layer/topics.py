from orders.events import Event, OrderApprovedEvent, OrderCreatedEvent, OrderRejectedEvent

TOPICS_MAP: dict[type[Event], str] = {
    OrderCreatedEvent: "order--created",
    OrderApprovedEvent: "order--approved",
    OrderRejectedEvent: "order--rejected",
}
