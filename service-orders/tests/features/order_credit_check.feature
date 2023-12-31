Feature: Order credit check

    Background:
        Given an order is created with total amount of "100.99"

    Scenario: Credit check passed for a new order
        When CustomerCreditReserved event is received
        Then the order state is "APPROVED"
        And the OrderApproved event is published

    Scenario: Credit check failed for a new order
        When CustomerCreditReservationFailed event is received
        Then the order state is "REJECTED"
        And the OrderRejected event is published
