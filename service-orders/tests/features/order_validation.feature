Feature: Order validation

    Scenario: Reject order if customer validation failed
        Given an order exists in "PENDING" state
        When CustomerValidationFailed event is received
        Then the order state is "REJECTED"
        And the OrderRejected event is published
