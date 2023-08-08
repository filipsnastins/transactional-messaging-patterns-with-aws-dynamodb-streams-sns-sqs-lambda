Feature: Cancel order

    Scenario: Cancel order
        Given an order in "APPROVED" state
        When order cancellation is requested
        Then order cancellation request succeeded
        And the order state is "CANCELLED"
        And the OrderCancelled event is sent

    Scenario: Pending order cancellation is not allowed
        Given an order in "PENDING" state
        When order cancellation is requested
        Then order cancellation request failed - pending order cannot be cancelled
        And the order state is "PENDING"
        And the OrderCancelled event is not sent
