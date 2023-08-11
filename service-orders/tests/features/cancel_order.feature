Feature: Cancel order

    Background:
        Given an order is created with total amount of "100.99"

    Scenario: Cancel order
        Given CustomerCreditReserved event is received
        And the order state is "APPROVED"
        When order cancellation is requested
        Then the order cancellation request succeeded
        And the order state is "CANCELLED"
        And the OrderCancelled event is published

    Scenario: Pending order cancellation is not allowed
        Given the order state is "PENDING"
        When order cancellation is requested
        Then the order cancellation request failed - "CANNOT_CANCEL_PENDING_ORDER"
        And the order state is "PENDING"
