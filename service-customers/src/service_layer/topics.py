from customers.events import CustomerCreatedEvent, Event

CUSTOMER_TOPICS_MAP: dict[type[Event], str] = {
    CustomerCreatedEvent: "customer--created",
}
