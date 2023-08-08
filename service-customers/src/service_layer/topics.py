from customers.events import (
    CustomerCreatedEvent,
    CustomerCreditReservationFailedEvent,
    CustomerCreditReservedEvent,
    CustomerValidationFailedEvent,
    Event,
)

TOPICS_MAP: dict[type[Event], str] = {
    CustomerCreatedEvent: "customer--created",
    CustomerCreditReservedEvent: "customer--credit-reserved",
    CustomerCreditReservationFailedEvent: "customer--credit-reservation-failed",
    CustomerValidationFailedEvent: "customer--validation-failed",
}
