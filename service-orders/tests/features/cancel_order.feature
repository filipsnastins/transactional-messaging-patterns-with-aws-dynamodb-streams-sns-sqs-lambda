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
        Then pending order cannot be cancelled error is returned
        And the order state is "PENDING"

    Scenario: Cancel already cancelled order is idempotent
        Given CustomerCreditReserved event is received
        And the order state is "APPROVED"
        And order cancellation is requested
        And the order cancellation request succeeded
        And the order state is "CANCELLED"
        And the OrderCancelled event is published
        When order cancellation is requested
        Then the order cancellation request succeeded
        And the order state is "CANCELLED"
        And the OrderCancelled event is not published
