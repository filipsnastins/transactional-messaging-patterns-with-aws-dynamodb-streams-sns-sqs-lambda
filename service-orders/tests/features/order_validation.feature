Feature: Order validation

    Scenario: Reject order if customer validation failed
        Given an order is created with total amount of "100.99"
        When CustomerValidationFailed event is received
        Then the order state is "REJECTED"
        And the OrderRejected event is published
