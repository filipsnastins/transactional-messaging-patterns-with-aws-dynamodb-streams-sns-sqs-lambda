from customers.events import (
    CustomerCreatedEvent,
    CustomerCreditReservationFailedEvent,
    CustomerCreditReservedEvent,
    CustomerValidationFailedEvent,
    Event,
)

TOPICS_MAP: dict[type[Event], str] = {
    CustomerCreatedEvent: "customer--created",
    CustomerCreditReservationFailedEvent: "customer--credit-reservation-failed",
    CustomerCreditReservedEvent: "customer--credit-reserved",
    CustomerValidationFailedEvent: "customer--validation-failed",
}
