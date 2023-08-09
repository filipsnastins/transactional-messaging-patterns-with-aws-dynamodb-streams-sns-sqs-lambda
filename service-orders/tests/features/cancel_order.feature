Feature: Cancel order

    Scenario: Cancel order
        Given an order exists in "APPROVED" state
        When order cancellation is requested
        Then the order cancellation request succeeded
        And the order state is "CANCELLED"
        And the OrderCancelled event is published

    Scenario: Pending order cancellation is not allowed
        Given an order exists in "PENDING" state
        When order cancellation is requested
        Then the order cancellation request failed - pending order cannot be cancelled
        And the order state is "PENDING"
